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
In order to deploy the app on a Balena.io Fleet, the balena-cli tool must be installed. This tool is available for installing on [Linux](https://github.com/balena-io/balena-cli/blob/master/INSTALL-LINUX.md), [Windows](https://github.com/balena-io/balena-cli/blob/master/INSTALL-WINDOWS.md), and [macOS](https://github.com/balena-io/balena-cli/blob/master/INSTALL-MAC.md). After this tool is installed, run the following commands from the current directory of this repository:

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
