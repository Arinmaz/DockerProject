FROM python:3.10-alpine
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Ensure that .env file is copied
COPY .env .env

CMD ["python3", "app.py"]
