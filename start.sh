#!/bin/bash

# Start each command in the background
python Capture/picamera.py Config.json &
python Motion/motion.py Config.json &
python Classify/classify_image.py Config.json &
python Upload/upload_edge.py Config.json &
python Upload/upload_telegram.py Config.json &

# Wait for all background jobs to finish
wait
