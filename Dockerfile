FROM python:3.9-slim

# Install necessary system dependencies
RUN apt update && \
    apt install -y libsndfile1 ffmpeg libsm6 libxext6 libgl1 build-essential curl software-properties-common libcap-dev portaudio19-dev && \
    apt clean

# Install Node.js and npm
RUN apt update && \
    apt install -y nodejs npm

# Install Edge Impulse CLI
RUN npm install edge-impulse-linux -g --unsafe-perm

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
