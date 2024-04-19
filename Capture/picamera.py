# from picamera2 import Picamera2, Preview
from random import randint
import os
import time
import datetime
import sys, getopt
import signal
import config_loader
import cv2
import threading
from telegram import Bot
import asyncio
#used for closing
picam2=None
is_capture_time = False

async def send_telegram_message(channel_id, token, message):
    bot = Bot(token=token)
    await bot.send_message(chat_id=channel_id, text=message)

def is_time_to_capture():
    """
    Determine if the current time is within the scheduled capture range for the current day of the week.        
    Returns:
        bool: True if the current time is within the range, False otherwise.
    """
    now = datetime.datetime.now()
    day_of_week = now.strftime('%A').upper()  # Get the current day of the week in all caps, e.g., "MONDAY"
    start_time_str = config_loader.get_value(f"CAPTURE_SCHEDULE_{day_of_week}_START")
    end_time_str = config_loader.get_value(f"CAPTURE_SCHEDULE_{day_of_week}_END")
    # Check if both start and end times are empty first
    if start_time_str == "" and end_time_str == "":
        print(f"Capture schedule for {day_of_week} is not set.")
        return False
    # Then, set default values for missing start or end times
    if start_time_str == "":
        start_time_str = "00:00"
    if end_time_str == "":
        end_time_str = "23:59"
    # Parse and construct datetime objects for comparison
    start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
    end_time = datetime.datetime.strptime(end_time_str, '%H:%M').time()
    current_time = now.time()
    # Adjust for dates when end time is next day
    if start_time >= end_time:
        raise ValueError("Start time cannot be later than end time for the day.")
    # Check if the current time is within the start and end time range
    return not (start_time <= current_time <= end_time)

def update_capture_status(update_interval=30):
    """
    Periodically update the global capturing status.
    
    Args:
        config_loader: Configuration loader to fetch schedule.
        update_interval (int): How often to update the status, in seconds.
    """
    global is_capture_time
    while True:
        try:
            is_capture_time = is_time_to_capture()
        except Exception as e:
            print(f"Error updating capture status: {e}")
        time.sleep(update_interval)

def keep_fps( start_time,final_time, fps):
    fps_real = 1 / (final_time - start_time)
    if fps_real < fps:
        pass
    elif fps_real >= fps:
        time.sleep((fps_real - fps) / (fps * fps_real))

#Ctrl C catch and close
def handler(signum, frame):
    print("closing")
    picam2.close()
    exit(1)

def main(argv):
    global picam2
    while True:
        try:
            opts, args = getopt.getopt(argv, "h", ["--help"])
        except getopt.GetoptError:
            sys.exit(2)
        config_loader.load_config(args[0])
        TOKEN = config_loader.get_value("ALERT_TOKEN")
        channel_id = config_loader.get_value("ALERT_CHANNELID")
        status_thread = threading.Thread(target=update_capture_status, args=())
        status_thread.start()
        if not is_capture_time:
            time.sleep(5)
            continue
        if config_loader.get_value("CAPTURE_PICAMERA_FPS") == 0:
            try:
                fps_needed = float(config_loader.get_value("CAPTURE_STREAM_FPS"))
                vcap = cv2.VideoCapture(config_loader.get_value("CAPTURE_STREAM_URL"), cv2.CAP_FFMPEG)
                while True:
                    start_time=time.time()
                    ret, frame = vcap.read()
                    if ret == False:
                        print("Frame is empty, stream is not available!")
                        raise Exception("Frame is empty, stream is not available!")
                    else:
                        now = datetime.datetime.now()
                        cv2.imwrite(os.path.join(config_loader.get_value("DATAFOLDER"), 'captured', f'{now.strftime("%Y%m%d%H%M%S%f")}.jpg'), frame)
                    keep_fps(start_time,time.time(),fps_needed)
                    if not is_capture_time:
                        vcap.release()
                        break
                vcap.release()
            except Exception as ex:
                print(f'Camera stream from camera {config_loader.get_value("CAPTURE_NAME")} available on url {config_loader.get_value("CAPTURE_STREAM_URL")} is not available or failed: {ex}, retrying in 5 minutes')
                loop = asyncio.get_event_loop()
                loop.run_until_complete(send_telegram_message(channel_id, TOKEN, f'Camera stream {config_loader.get_value("CAPTURE_STREAM_URL")} is not available or failed: {ex}, retrying in 5 minutes'))
                time.sleep(300)
        else:
            try:
                fps_needed = float(config_loader.get_value("CAPTURE_PICAMERA_FPS"))

                #initiate Picamera and set configure size photo
                picam2 = Picamera2()
                preview_config = picam2.preview_configuration(main={"size": (800, 600),"ExposureTime": 1000})
                picam2.configure(preview_config)
                picam2.start()

                time.sleep(2)

                #catch Ctrl C
                signal.signal(signal.SIGINT, handler)
                #loop and save captured image every x seconds
                while True:
                    start_time = time.time()
                    now = datetime.datetime.now()

                    metadata = picam2.capture_file(os.path.join(config_loader.get_value("DATAFOLDER"), 'captured', f'{now.strftime("%Y%m%d%H%M%S%f")}.jpg'))
                    if config_loader.get_value("DEBUG") == 1:
                        metadata = picam2.capture_file(config_loader.get_value("DATAFOLDER")+'/debug/capture.jpg')
                    if config_loader.get_value("DEBUG") == 1:
                        print(metadata)

                    keep_fps(start_time,time.time(),fps_needed)
                    if not is_capture_time:
                        picam2.close()
                        break
            except Exception as ex:
                print(f'Picamera is not available or failed: {ex}, retrying in 5 minutes')
                loop = asyncio.get_event_loop()
                loop.run_until_complete(send_telegram_message(channel_id, TOKEN, f'Picamera is not available or failed: {ex}, retrying in 5 minutes'))
                time.sleep(300)
        time.sleep(5)


if __name__ == "__main__":
   main(sys.argv[1:])