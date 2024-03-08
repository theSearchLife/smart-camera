FROM node:latest

# Install necessary system dependencies
RUN apt update && \
    apt install -y python3 python3-pip libsndfile1 ffmpeg libsm6 libxext6 libgl1 build-essential curl software-properties-common libcap-dev portaudio19-dev && \
    apt clean

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
