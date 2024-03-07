#!/bin/bash

# Start each command in the background
python3 Classify/download_model.py Config.json &
python3 Capture/picamera.py Config.json &
python3 Motion/motion.py Config.json &
python3 Classify/classify_image.py Config.json &
python3 Upload/upload_edge.py Config.json &
python3 Upload/upload_telegram.py Config.json &

# Wait for all background jobs to finish
wait
