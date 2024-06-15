# Use official MongoDB image as the base
FROM mongo:5

# Copy the initialization script into the container
COPY init.sh /docker-entrypoint-initdb.d/init.sh

# Set permissions for the script to be executable
RUN chmod +x /docker-entrypoint-initdb.d/init.sh
