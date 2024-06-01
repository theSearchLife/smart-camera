![Workflow](img/workflow.png)

Introduction
============

This project aims to reduce Human-wildlife conflict with the help of video surveillance and artificial intelligence.
The idea is to use a camera for 24h video surveillance and machine learning to detect and alert for animals that pose a threat livelihood or safety of the people in the area. Due to GDPR reasons, a pause of video recording during a time interval specific to each day of the week is implemented.

Structure of the app
=========
This app is a GitHub Registry Container (GHRC), container that is created with the help of a GitHub workflow present in *.github/workflows/main.yml*. Since our app is designed as a container on GHRC, with the name of *ghcr.io/thesearchlife/smart-camera:latest*, we have a Dockerfile that contains all the necesarry instructions to run the app, such as installing all the packages and Python modules, setting the timezone using the script *set_timezone.sh*, as well as run the *start.sh* script that starts all the Python scripts used in this app, scripts that are described below. We also have a *docker-compose.yml* file used for deploying the GHRC container on a Balena.io fleet of our choice.

The app consists of 3 main modules:
 - **The model downloading module**: present in Python script *Detection/download_model.py*, this module downloads the model trained on the Edge Impulse platform every 24 hours.
 - **The detection module**: present in Python script *Detection/capture_motion_detection.py*, this module captures frames from the video stream specified inside the *Config.json* file, performs motion detection over a given perimeter and, using a convolutional neural network called YOLOv5 trained on Edge Impulse platform, detects the presence of the desired entity we wish to identify; if such entity is present in the current frame, we are saving a GIF or a photo collage that consists of the moment of the detection together with an pre-established number of frames from before that moment, as well as a picture of the frame the detection was encountered, picture that is going to be uploaded on the Edge Impulse platform in order to improve the object detection model; after the GIF or the photo collage is saved, it is uploaded on Telegram as an alert.
 - **The Edge Impulse module**: present in Python script *Upload/upload_edge.py*, this module uploads all the pictures on Edge Impulse platform that are going to be used for further training the model.

How to install the app
==============
Here are the steps required to install the Smart Cam App on an IoT device (e.g. Raspberry Pi 5):
1. Install balenaOS on the embedded device and balena CLI on a computer used for deployment and development, create a balena device fleet, as well as add the IoT device in that fleet by following the steps from the [official guide](https://docs.balena.io/learn/getting-started/raspberrypi5/python/).
2. Establish values and create the environment variables of the fleet on the balena Cloud platform; these fleet environment variables are:
    - **ALERT_CHANNELID** - the ID of the Telegram channel that is going to be used to upload the alerts of the Smart Cam App;
    - **ALERT_TOKEN** - the token of the Telegram Bot used for uploading the alerts on the Telegram alert channel;
    - **ALERT_NUMFRAMES** - the number of frames that are going to be put inside the GIF or photo collage corresponding to a detection;
    - **ALERT_SAVEGIF** - boolean value (0 or 1) that determines whether we save the detection as a GIF for 1 or as a photo collage for 0;
    - **CAPTURE_NAME** - the name of the video live stream that is used in the app;
    - **CAPTURE_STREAM_URL** - the URL of the video live stream that is used in the app;
    - **DETECTION_APIKEY** - the Edge Impulse API key used for interacting with the correspondent Edge Impulse project, such as uploading the pictures used for improving the model or downloading the model;
    - **DETECTION_INTERVAL** - the minimum amount of seconds between two detections and two Telegram uploads, subsequently;
    - **DETECTION_THRESHOLD** - the minimum confidence of a detection;
    - **MOTION_ROI_XMIN** - the X coordinate of the upper-left point of the ROI (*region of interest*) used in the motion detection algorithm;
    - **MOTION_ROI_XMAX** - the Y coordinate of the upper-left point of the ROI (*region of interest*) used in the motion detection algorithm;
    - **MOTION_ROI_YMIN** - the X coordinate of the bottom-right point of the ROI (*region of interest*) used in the motion detection algorithm;
    - **MOTION_ROI_YMAX** - the Y coordinate of the bottom-right point of the ROI (*region of interest*) used in the motion detection algorithm;
    - **CAPTURE_SCHEDULE_MONDAY_START** - the start hour in format *HH:MM* of the recording pause on Monday;
    - **CAPTURE_SCHEDULE_MONDAY_END** - the end hour in format *HH:MM* of the recording pause on Monday;
    - **CAPTURE_SCHEDULE_TUESDAY_START** - the start hour in format *HH:MM* of the recording pause on Tuesday;
    - **CAPTURE_SCHEDULE_TUESDAY_END** - the end hour in format *HH:MM* of the recording pause on Tuesday;
    - **CAPTURE_SCHEDULE_WEDNESDAY_START** - the start hour in format *HH:MM* of the recording pause on Wednesday;
    - **CAPTURE_SCHEDULE_WEDNESDAY_END** - the end hour in format *HH:MM* of the recording pause on Wednesday;
    - **CAPTURE_SCHEDULE_THURSDAY_START** - the start hour in format *HH:MM* of the recording pause on Thursday;
    - **CAPTURE_SCHEDULE_THURSDAY_END** - the end hour in format *HH:MM* of the recording pause on Thursday;
    - **CAPTURE_SCHEDULE_FRIDAY_START** - the start hour in format *HH:MM* of the recording pause on Friday;
    - **CAPTURE_SCHEDULE_FRIDAY_END** - the end hour in format *HH:MM* of the recording pause on Friday;
    - **CAPTURE_SCHEDULE_SATURDAY_START** - the start hour in format *HH:MM* of the recording pause on Saturday;
    - **CAPTURE_SCHEDULE_SATURDAY_END** - the end hour in format *HH:MM* of the recording pause on Saturday;
    - **CAPTURE_SCHEDULE_SUNDAY_START** - the start hour in format *HH:MM* of the recording pause on Sunday;
    - **CAPTURE_SCHEDULE_SUNDAY_END** - the end hour in format *HH:MM* of the recording pause on Sunday;
3. Once these fleet variables are added, deploy the Smart Cam app on the balenaCloud fleet using these commands: 
    ```bash
    balena login  # used only once in order to login into the Balena Cloud account
    balena push <balena-cloud-fleet-name>  # push the service on your desired fleet, e.g.: gh_omegamax10/thesearchlife-smart-camera
    ```
    The collected data of this fleet is placed on the host device of the fleet in the following location: `/var/lib/docker/volumes/<APP ID>_smart-camera-data/_data`. This location stores the data from the `Data/` folder of the container.


How to view logs of the Smart-Camera service on devices of a Balena fleet
==========
In order to see the logs of the Smart-Camera service on a device of a fleet, we must activate persistent logging in the fleet configuration on Balena Cloud. The logs the can be viewed with the following command:

```bash
journalctl -a --no-pager -u balena.service --file /var/log/journal/<machine-id>/system.journal  # Replace <machine-id> with the unique system identifier to view balena.service logs from the specified journal file, e.g.:cdc38b4575d543bab0fc166e5f1fba07; the machine-id can be found in /etc/machine-id
```


How to download files from within the Smart Camera service on a local machine
=======================
In order to download a file from within the container on a local machine, we are going to use an online tool called [Tool.sh](https://temp.sh/). We are going to use the following command from within the terminal of the container that can be accessed from the summary of the device from Balena Dashboard:
```bash
curl -F "file=@Data/model/model.eim" https://temp.sh/upload && echo
```
This command will output a link to Tool.sh that can be accesed in order to download the desired file locally.

Useful Edge Impulse CLI commands
================
In order to use the Edge Impulse CLI on a Linux machine, make sure that you install NPM, and, after that, install Edge Impulse CLI with the following commands:
```bash
npm install edge-impulse-linux -g --unsafe-perm
npm install -g edge-impulse-cli
```

An useful Edge Impulse API command would be the one corresponding to downloading the model from an Edge Impulse project. First, create the API key inside the project dashboard "Keys" section, save it in a secure place and use the following command to download the Edge Impulse model corresponding to that project:
```bash
edge-impulse-linux-runner --download ./Data/model/model.eim --api-key <edge-impulse-api-key>
```

Another useful Edge Impulse API command would be the one corresponding to uploading an image or multiple images to an Edge Impulse project, image used for training or improving the model used in this app. An example of such a command is as follows:
```bash
edge-impulse-uploader --api-key <edge-impulse-api-key> .Data/detected/*.jpg
```
This command uploads all the JPEG images present in folder "Data/detected/" in the project, with the purpose of training or improving the model corresponding to the Edge Impulse project.
