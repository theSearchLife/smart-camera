FROM python:3.9-slim
RUN apt update && \
    apt install -y libsndfile1 ffmpeg libsm6 libxext6 libgl1 build-essential curl software-properties-common libcap-dev portaudio19-dev libatlas-base-dev libportaudio0 libportaudio2 libportaudiocpp0 libopenjp2-7 libgtk-3-0 libswscale-dev libavformat58 libavcodec58 && \
    apt clean

WORKDIR /smart-camera
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh
CMD ["./start.sh"]
