# from picamera2 import Picamera2, Preview
from random import randint

import time
import datetime
import sys, getopt
import signal
import config_loader
import cv2

#used for closing
picam2=None

def is_time_to_capture(start_time_str, end_time_str):
    """
    Check if the current time is within a specified range, potentially spanning over midnight.
    Args:
        start_time_str (str): The start time in "HH:MM" format.
        end_time_str (str): The end time in "HH:MM" format.
    Returns:
        bool: True if the current time is within the range, False otherwise.
    """
    now = datetime.datetime.now()
    start_time_params = [int(x) for x in start_time_str.split(":")]
    end_time_params = [int(x) for x in end_time_str.split(":")]
    start_time = now.replace(hour=start_time_params[0], minute=start_time_params[1], second=0, microsecond=0)
    end_time = now.replace(hour=end_time_params[0], minute=end_time_params[1], second=59, microsecond=999999)
    if end_time <= start_time:
        if now < end_time:
            start_time -= datetime.timedelta(days=1)
        else:
            end_time += datetime.timedelta(days=1)
    return start_time <= now < end_time

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
        start_time_str = config_loader.get_value("CAPTURE_STARTTIME")
        end_time_str = config_loader.get_value("CAPTURE_ENDTIME")
        if not is_time_to_capture(start_time_str, end_time_str):
            time.sleep(60)
            continue
        if config_loader.get_value("CAPTURE_PICAMERA_FPS") == 0:
            try:
                fps_needed = float(config_loader.get_value("CAPTURE_STREAM_FPS"))
                vcap = cv2.VideoCapture(config_loader.get_value("CAPTURE_STREAM_URL"), cv2.CAP_FFMPEG)
                while True:
                    start_time=time.time()
                    ret, frame = vcap.read()
                    if ret == False:
                        print("Frame is empty")
                        break
                    else:
                        now = datetime.datetime.now()
                        cv2.imwrite(config_loader.get_value("DATAFOLDER")+'/captured/'+str(now.hour)+str(now.minute)+str(now.second)+str(randint(0, 100))+'.jpg', frame)
                    keep_fps(start_time,time.time(),fps_needed)

                vcap.release()
            except Exception as ex:
                print(ex)

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

                    metadata = picam2.capture_file(config_loader.get_value("DATAFOLDER")+'/captured/'+str(now.hour)+str(now.minute)+str(now.second)+str(randint(0, 100))+'.jpg')
                    if config_loader.get_value("DEBUG") == 1:
                        metadata = picam2.capture_file(config_loader.get_value("DATAFOLDER")+'/debug/capture.jpg')
                    if config_loader.get_value("DEBUG") == 1:
                        print(metadata)

                    keep_fps(start_time,time.time(),fps_needed)
            except Exception as ex:
                print(ex)
        time.sleep(5)


if __name__ == "__main__":
   main(sys.argv[1:])