# from picamera2 import Picamera2, Preview
from random import randint
import os
import time
import imageio
import datetime
import sys, getopt
import signal
import config_loader
import cv2
import threading
from telegram import Bot, error
import asyncio
import numpy as np
from edge_impulse_linux.image import ImageImpulseRunner
from collections import deque
from PIL import Image

#used for closing
picam2=None
is_capture_time = False
runner = None

def pad_image(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    aspect_ratio = img.shape[1] / img.shape[0]
    longest_side = max(img.shape[0], img.shape[1])
    square_img = np.zeros((longest_side, longest_side, 3), np.uint8)
    x_offset = (longest_side - img.shape[1]) // 2
    y_offset = (longest_side - img.shape[0]) // 2
    square_img[y_offset:y_offset+img.shape[0], x_offset:x_offset+img.shape[1]] = img
    return square_img, aspect_ratio

def restore_image(cropped, aspect_ratio):
    # cropped is a square image, restore it to the original aspect ratio by removing padding
    if aspect_ratio > 1:
        new_width = int(cropped.shape[0] / aspect_ratio)
        cropped = cropped[(cropped.shape[0] - new_width) // 2:(cropped.shape[0] - new_width) // 2 + new_width, :]
    else:
        new_height = int(cropped.shape[1] * aspect_ratio)
        cropped = cropped[:, (cropped.shape[1] - new_height) // 2:(cropped.shape[1] - new_height) // 2 + new_height]
    return cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR)

class Rois():
    def __init__(self):
        self.listRois=list()

    def choose_ROIs(self,frame):
        self.frame=frame
        self.save=frame
        self.listRois=[(int(config_loader.get_value("MOTION_ROI_XMIN")),
                        int(config_loader.get_value("MOTION_ROI_YMIN")),
                        int(config_loader.get_value("MOTION_ROI_XMAX")),
                        int(config_loader.get_value("MOTION_ROI_YMAX")))]
        
    def check_if_overlapping(self, x, y, w, h):
        for roi in self.listRois:
            return not (roi[0][0]+roi[1][0] < x or roi[0][0] > x+w or roi[0][1] < y+h or roi[0][1]+roi[1][1] > y)

    def overlap(self,frame1, x, y, w, h):
        for roi in self.listRois:
            #sunt inversate, e x1 si y1 jos stanga
            newx1=x
            newx2=x+w
            newy2=y
            newy1=y+h
            x1=roi[0]
            x2=roi[2]
            y2=roi[1]
            y1=roi[3]

            # if config_loader.get_value("DEBUG") == 1:
            #     cv2.rectangle(frame1, (x1, y1), (x2, y2), (0, 255, 0), 2)
            if (x1 < newx2 and x2 > newx1 and
                    y1 > newy2 and y2 < newy1):
                return True
        return False

async def send_telegram_message(bot, channel_id, message):
    await bot.send_message(chat_id=channel_id, text=message)

async def send_photo_async(bot, channel_id, photo_path):
    try:
        await asyncio.sleep(1)  # Implementing delay between each message to prevent rate limiting
        with open(photo_path, 'rb') as photo:
            media_type = photo_path.lower().split('.')[-1]
            if media_type == 'gif':
                await bot.send_animation(chat_id=channel_id, animation=photo, caption=f'Detection from camera with name {config_loader.get_value("CAPTURE_NAME")} in {photo_path}', read_timeout=5, write_timeout=20, connect_timeout=5, pool_timeout=5)
            elif media_type == 'mp4':
                await bot.send_video(chat_id=channel_id, video=photo, caption=f'Detection from camera with name {config_loader.get_value("CAPTURE_NAME")} in {photo_path}', read_timeout=5, write_timeout=20, connect_timeout=5, pool_timeout=5)
            elif media_type == 'jpg':
                await bot.send_photo(chat_id=channel_id, photo=photo, caption=f'Detection from camera with name {config_loader.get_value("CAPTURE_NAME")} in {photo_path}', read_timeout=5, write_timeout=20, connect_timeout=5, pool_timeout=5)
    except error.BadRequest as e:
        if "File must be non-empty" in str(e):
            print(f"Caught empty file error for {photo_path}. Retrying...")
            await asyncio.sleep(3)  # Delay to allow time for the file to be ready
            await send_photo_async(bot, channel_id, photo_path)  # Retry sending the photo
        else:
            raise
    except error.TimedOut as te:
        print(f"Timeout error: {te}. Retrying...")
        await asyncio.sleep(te.retry_after if hasattr(te, "retry_after") else 10)  # Wait before retrying
        await send_photo_async(bot, channel_id, photo_path)  # Retry sending the photo       
    except Exception as e:
        print(f"An error occurred: {e}")

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

def save_gif(frame_list):
    gamma = 1.01
    lut = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)]).astype("uint8")
    frame_list = list(frame_list)
    last_frame = frame_list[-1].copy()
    extension = [last_frame, cv2.LUT(last_frame, lut)]
    for _ in range(5):
        frame_list.extend(extension)
    gif_path = os.path.join(config_loader.get_value("DATAFOLDER"), 'detectedTelegram', f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")}.gif')
    pil_images = [Image.fromarray(frame) for frame in frame_list]
    pil_images[0].save(gif_path, save_all=True, append_images=pil_images[1:], duration=500, loop=0, optimize=True)
    # imageio.mimsave(gif_path, frame_list, duration=500)
    return gif_path

def save_mp4(frame_list):
    mp4_path = os.path.join(config_loader.get_value("DATAFOLDER"), 'detectedTelegram', f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")}.mp4')
    out = cv2.VideoWriter(mp4_path, cv2.VideoWriter_fourcc(*'mp4v'), 1, (frame_list[0].shape[1], frame_list[0].shape[0]))
    for frame in frame_list:
        out.write(frame)
    out.release()
    return mp4_path

def main(argv):
    global picam2
    time.sleep(15)
    while True:
        try:
            opts, args = getopt.getopt(argv, "h", ["--help"])
        except getopt.GetoptError:
            sys.exit(2)
        config_loader.load_config(args[0])

        modelfile = config_loader.get_value("DETECTION_NETWORK")
        detection_time_interval = float(config_loader.get_value("DETECTION_INTERVAL"))
        last_detection_time = datetime.datetime(datetime.MINYEAR, 1, 1, 0, 0, 0, 0)
        current_detection_time = datetime.datetime(datetime.MINYEAR, 1, 1, 0, 0, 0, 0)
        print('MODEL: ' + modelfile)

        with ImageImpulseRunner(modelfile) as runner:
            try:
                model_info = runner.init()
                print('Loaded runner for "' + model_info['project']['owner'] + ' / ' + model_info['project']['name'] + '"')
                labels = model_info['model_parameters']['labels']
                bot = Bot(token=config_loader.get_value("ALERT_TOKEN"))
                channel_id = config_loader.get_value("ALERT_CHANNELID")
                status_thread = threading.Thread(target=update_capture_status, args=())
                status_thread.start()
                if not is_capture_time:
                    time.sleep(5)
                    continue
                if config_loader.get_value("CAPTURE_PICAMERA_FPS") == 0:
                    try:
                        frame_list = deque(maxlen=int(config_loader.get_value("ALERT_NUMFRAMES")))
                        # fps_needed = float(config_loader.get_value("CAPTURE_STREAM_FPS"))  # COMMENT THIS
                        vcap = cv2.VideoCapture(config_loader.get_value("CAPTURE_STREAM_URL"), cv2.CAP_FFMPEG)
                        ret, prev_frame = vcap.read()
                        if ret == False:
                            print("Frame is empty, stream is not available!")
                            raise ValueError("Frame is empty, stream is not available!")
                        RoisClass = Rois()
                        RoisClass.choose_ROIs(prev_frame)
                        while True:
                            # start_time=time.time()  # COMMENT THIS
                            ret, frame = vcap.read()
                            if ret == False:
                                print("Frame is empty, stream is not available!")
                                raise ValueError("Frame is empty, stream is not available!")
                            else:
                                # cv2.putText(frame, datetime.datetime.now().strftime("%H:%M:%S"), (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
                                diff = cv2.absdiff(prev_frame, frame)
                                gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                                blur=cv2.GaussianBlur(gray,(5,5),0)
                                _,thresh = cv2.threshold(blur,20, 255, cv2.THRESH_BINARY)
                                dilated = cv2.dilate(thresh,None, iterations=3)
                                contours,_ = cv2.findContours(dilated,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
                                is_motion = False
                                for contour in contours:
                                    (x,y,w,h) = cv2.boundingRect(contour)
                                    if cv2.contourArea(contour) < 700:
                                        continue
                                    if RoisClass.overlap(prev_frame, x, y, w, h):
                                        print(f'Motion at {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
                                        square_img, aspect_ratio = pad_image(frame)
                                        features, cropped = runner.get_features_from_image(square_img)
                                        res = runner.classify(features)
                                        if "classification" in res["result"].keys():
                                            if config_loader.get_value("DEBUG") == 1:
                                                print('Result (%d ms.) ' % (res['timing']['dsp'] + res['timing']['classification']), end='')
                                            for label in labels:
                                                score = res['result']['classification'][label]
                                                if config_loader.get_value("DEBUG") == 1:
                                                    print('%s: %.2f\t' % (label, score), end='')
                                            print('', flush=True)
                                        elif "bounding_boxes" in res["result"].keys():
                                            if config_loader.get_value("DEBUG") == 1:
                                                print('Found %d bounding boxes (%d ms.)' % (len(res["result"]["bounding_boxes"]), res['timing']['dsp'] + res['timing']['classification']))
                                            for bb in res["result"]["bounding_boxes"]:
                                                if config_loader.get_value("DEBUG") == 1:
                                                    print('\t%s (%.2f): x=%d y=%d w=%d h=%d' % (bb['label'], bb['value'], bb['x'], bb['y'], bb['width'], bb['height']))
                                                if bb['value'] > float(config_loader.get_value("DETECTION_THRESHOLD")):
                                                    current_detection_time = datetime.datetime.now()
                                            if (current_detection_time - last_detection_time).total_seconds() > detection_time_interval:
                                                if config_loader.get_value("DETECTION_UPLOADEDGE") == 1:
                                                    cv2.imwrite(os.path.join(config_loader.get_value("DATAFOLDER"), 'detected', f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")}.jpg'),  restore_image(cropped, aspect_ratio))
                                            for bb in res["result"]["bounding_boxes"]:
                                                if bb['value'] > float(config_loader.get_value("DETECTION_THRESHOLD")):
                                                    cropped = cv2.rectangle(cropped, (bb['x'], bb['y']), (bb['x'] + bb['width'], bb['y'] + bb['height']), (255, 0, 0), 1)
                                                    (text_width, text_height), _ = cv2.getTextSize(f"{bb['label']}: {bb['value']:.2f}", cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                                                    cropped = cv2.rectangle(cropped, (bb['x'], bb['y']-text_height - 5), (bb['x']+text_width, bb['y']), (255, 0, 0), -1)
                                                    cropped = cv2.putText(cropped, f"{bb['label']}: {bb['value']:.2f}", (bb['x'], bb['y'] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                                        frame_list.append(cv2.cvtColor(restore_image(cropped, aspect_ratio), cv2.COLOR_BGR2RGB))
                                        if (current_detection_time - last_detection_time).total_seconds() > detection_time_interval:
                                            last_detection_time = current_detection_time
                                            gif_path = save_gif(frame_list)
                                            # loop = asyncio.get_event_loop()
                                            # loop.run_until_complete(send_photo_async(bot, channel_id, gif_path))
                                            # os.remove(gif_path)
                                        is_motion = True
                                        break
                                if is_motion == False:
                                    square_img, aspect_ratio = pad_image(frame)
                                    square_img = cv2.resize(square_img, (model_info['model_parameters']['image_input_height'], model_info['model_parameters']['image_input_width']), interpolation=cv2.INTER_AREA)
                                    frame_list.append(cv2.cvtColor(restore_image(square_img, aspect_ratio), cv2.COLOR_BGR2RGB))
                                prev_frame = frame.copy()
                                del frame
                            # keep_fps(start_time,time.time(),fps_needed)  # COMMENT THIS
                            if not is_capture_time:
                                vcap.release()
                                break
                        vcap.release()
                    except ValueError as ex:
                        if config_loader.get_value("DEBUG") == 1:
                            print(f'Camera stream from camera {config_loader.get_value("CAPTURE_NAME")} available on url {config_loader.get_value("CAPTURE_STREAM_URL")} could not be read: {ex}.')
                    except Exception as ex:
                        print(f'Camera stream from camera {config_loader.get_value("CAPTURE_NAME")} available on url {config_loader.get_value("CAPTURE_STREAM_URL")} is not available or failed: {ex}, retrying in 5 minutes')
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(send_telegram_message(bot, channel_id, f'Camera stream {config_loader.get_value("CAPTURE_STREAM_URL")} is not available or failed: {ex}, retrying in 5 minutes'))
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
                        loop.run_until_complete(send_telegram_message(bot, channel_id, f'Picamera is not available or failed: {ex}, retrying in 5 minutes'))
                        time.sleep(300)
                time.sleep(1)
            
            finally:
                if (runner):
                    runner.stop()

if __name__ == "__main__":
   main(sys.argv[1:])