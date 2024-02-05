FROM python:3.11-slim-bookworm
RUN apt update && \
    apt install -y libsndfile1 ffmpeg libsm6 libxext6 libgl1 build-essential curl software-properties-common libcap-dev && \
    apt clean

WORKDIR /smart-camera
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN ["python", "classify-image.py", "Config.json"]
