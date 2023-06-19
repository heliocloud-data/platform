# syntax = docker/dockerfile:1.2

# Set base image (host OS)
FROM --platform=linux/amd64 python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip3 install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Specify the command to run on container start
CMD [ "python", "-u", "./app.py" ]