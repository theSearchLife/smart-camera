#!/bin/bash

# Fetch the timezone and set it as an environment variable
export TZ=$(curl -s https://ipinfo.io/timezone)
echo "Timezone set to $TZ"

python3 Classify/download_model.py Config.json &
python3 Capture/picamera.py Config.json &
python3 Motion/motion.py Config.json &
python3 Classify/classify_image.py Config.json &
python3 Upload/upload_edge.py Config.json &
python3 Upload/upload_telegram.py Config.json &
wait
