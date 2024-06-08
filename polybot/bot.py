import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
import boto3
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

s3client = boto3.client('s3')
images_bucket = os.environ['BUCKET_NAME']
class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class ObjectDetectionBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if self.is_current_msg_photo(msg):
            photo_path = self.download_user_photo(msg)
            unique_id = uuid.uuid4()
            object_name = f'photos/{unique_id}_{os.path.basename(photo_path)}'


            #  upload the photo to S3
            try:
                logger.info(f'file path : {photo_path}')
                logger.info(f'bucket_name : {images_bucket}')
                logger.info(f'object_name : {object_name}')

                s3client.upload_file(photo_path, images_bucket, object_name)
                # checking if the file is uploaded to s3
                max_attempts = 10
                for attempt in range(max_attempts):
                    response = s3client.list_objects_v2(Bucket=images_bucket, Prefix=object_name)
                    if 'Contents' in response:
                        logger.info("File is available on S3")
                        break
                    else:
                        logger.info("File is not available on S3 yet, retrying in 5 seconds...")
                        time.sleep(5)
                else:
                    raise TimeoutError("File upload time out. could not find file after 10 attempts")

                #  send an HTTP request to the `yolo5` service for prediction
                url = f'http://localhost:8081/predict?imgName={object_name}'
                logger.info(f'url : {url}')
                response = requests.post(url)
                if response.status_code == 200:
                    logger.info("Prediction succeeded!")
                    prediction_result = response.json()
                    self.send_text(msg['chat']['id'], f"Detection results: {prediction_result}")
                else:
                    logger.error(f"Prediction failed. Status code: {response.status_code}")
                    self.send_text(msg['chat']['id'], f"Prediction failed, please try again.")
            except Exception as e:
                logger.error(f"Error handling photo message: {e}")
                self.send_text(msg['chat']['id'], f"An error occurred: {e}")
        else:
            super().handle_message(msg)

            #  send the returned results to the Telegram end-user
