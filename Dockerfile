FROM node:latest

# Install necessary system dependencies
RUN apt update && \
    apt install -y python3 python3-pip python3-venv libsndfile1 ffmpeg libsm6 libxext6 libgl1 build-essential curl software-properties-common libcap-dev portaudio19-dev && \
    apt clean

# Install the edge-impulse-cli and edge-impulse-linux packages using npm
RUN npm install edge-impulse-linux -g --unsafe-perm
RUN npm install -g edge-impulse-cli

# Set the working directory
WORKDIR /smart-camera

# Create a Python virtual environment named smart-camera-venv and activate it
RUN python3 -m venv /smart-camera/smart-camera-venv
ENV PATH="/smart-camera/smart-camera-venv/bin:$PATH"

RUN export TZ=$(curl -s https://ipinfo.io/timezone)

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

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

# Expose NTP port
EXPOSE 123/udp

COPY set_timezone.sh /usr/local/bin/set_timezone.sh
RUN chmod +x /usr/local/bin/set_timezone.sh

# Ensure commands and scripts are run within the virtual environment
# by activating it
CMD ["/bin/bash", "-c", "source /smart-camera/smart-camera-venv/bin/activate && /usr/local/bin/set_timezone.sh && ./start.sh"]
