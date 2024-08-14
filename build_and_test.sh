#!/bin/bash

# Define the image name
IMAGE_NAME="omf-api-app"
CONTAINER_NAME="omf-api-container"
PORT=9048

# Function to check if the image exists
check_image_exists() {
    docker images -q $IMAGE_NAME
}

# Function to build the image
build_image() {
    echo "Building Docker image..."
    docker-compose build
}

# Function to run the container
run_container() {
    echo "Starting Docker container..."
    docker-compose up -d
}

# Function to test the application
test_application() {
    echo "Waiting for the container to start up..."
    sleep 10  # Give some time for the application to start

    echo "Testing the application..."
    curl -I http://localhost:$PORT

    if [ $? -eq 0 ]; then
        echo "Application is running successfully on port $PORT."
    else
        echo "Failed to connect to the application. Check the logs for details."
    fi
}

# Function to tear down the environment (Optional)
stop_container() {
    echo "Stopping Docker container..."
    docker-compose down
}

# Check if the image exists
IMAGE_ID=$(check_image_exists)

if [ -z "$IMAGE_ID" ]; then
    # Image not found, build it
    build_image
else
    echo "Docker image '$IMAGE_NAME' already exists. Skipping build."
fi

# Run the container
run_container

# Test the application
test_application

# Optionally, stop the container after testing (uncomment if needed)
# stop_container
chmod +x build_and_test.sh
