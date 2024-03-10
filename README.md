![Workflow](img/workflow.png)

Introduction
============

This project aims to reduce Human-wildlife conflict with the help of video surveillance and artificial intelligence.
The idea is to use a camera for 24h video surveillance and machine learning to detect and alert for animals that pose a threat livelihood or safety of the people in the area.

Structure
=========

Capture app stream - captures and saves photos from a cctv camera
Capture app - captures and saves photos from the camera connected to RaspberryPi
Motion app - performs motion detection over a given perimeter
Classify app - using neural network trained on Edge Impulse to detect objects in images from the input folder. Saves the images in which the objects of interest were found on "detected" folder
Upload Edge - upload images from "detected" folder to Edge Impulse Addnotation Queue
Upload Telegram - upload images from "detected" folder to Telegram group

How to install
==============

Install Python >3.9
Install requirements

```python
pip install -r requirements.txt
```

Install Edge Impulse CLI

How to run
==========

```python
python3 Classify/download_model.py Config.json

python3 Capture/picamera.py Config.json

python3 Motion/motion.py Config.json

python3 Classify/classify_image.py Config.json

python3 Upload/upload_edge.py Config.json

python3 Upload/upload_telegram.py Config.json
```

How to deploy on Balena Fleet
==========
