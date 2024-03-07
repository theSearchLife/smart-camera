#!/bin/bash

python3 Classify/download_model.py Config.json &
sleep 20
python3 Capture/picamera.py Config.json &
python3 Motion/motion.py Config.json &
python3 Classify/classify_image.py Config.json &
python3 Upload/upload_edge.py Config.json &
python3 Upload/upload_telegram.py Config.json &
wait
