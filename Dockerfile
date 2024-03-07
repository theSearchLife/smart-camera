FROM python:3.9-slim

# Install necessary system dependencies
RUN apt update && \
    apt install -y curl libsndfile1 ffmpeg libsm6 libxext6 libgl1 build-essential curl software-properties-common libcap-dev portaudio19-dev && \
    apt clean

# Install NVM (Node Version Manager)
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash

# Install Node.js using NVM
RUN nvm install node

# Create a directory for global npm packages
RUN mkdir ~/.npm-global

# Set the prefix for npm to the newly created directory
RUN npm config set prefix '~/.npm-global'

# Update the PATH environment variable to include the directory for global npm packages
RUN echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.profile

# Source the updated profile to use the updated PATH in the current session
RUN source ~/.profile

# Install the edge-impulse-cli using npm
RUN npm install -g edge-impulse-cli

# Set the working directory
WORKDIR /smart-camera

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create required directories
RUN mkdir -p /smart-camera/Data/captured \
    /smart-camera/Data/debug \
    /smart-camera/Data/detected \
    /smart-camera/Data/detectedTelegram \
    /smart-camera/Data/model \
    /smart-camera/Data/motion

# Copy the rest of your project
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

# Command to run your application
CMD ["./start.sh"]
