#!/bin/bash

# Fetch the timezone and set it as an environment variable
export TZ=$(curl -s https://ipinfo.io/timezone)
echo "Timezone set to $TZ"

python3 Detection/download_model.py Config.json &
python3 Detection/capture_motion_detection.py Config.json &
python3 Upload/upload_edge.py Config.json &
python3 Upload/upload_telegram.py Config.json &
wait
