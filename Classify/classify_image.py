#!/usr/bin/env python
import config_loader
import cv2
import os
import sys, getopt
import datetime
import time
import numpy as np
from edge_impulse_linux.image import ImageImpulseRunner

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

def main(argv):
    time.sleep(20)
    config_loader.load_config(argv[0])

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

            while True:
                dir_name=config_loader.get_value("DATAFOLDER")+'/motion/'
                # Get list of all files only in the given directory
                list_of_files = filter(lambda x: os.path.isfile(os.path.join(dir_name, x)), os.listdir(dir_name))
                # Sort list of files based on last modification time in ascending order
                list_of_files = sorted(list_of_files, key = lambda x: os.path.getmtime(os.path.join(dir_name, x)))
                # Iterate over sorted list of files and print file path along with last modification time of file 
                for file_name in list_of_files:
                    file_path = os.path.join(dir_name, file_name)
                    img = cv2.imread(file_path)
                    if img is None:
                        print('Failed to load image', file_path)
                        break
                    square_img, aspect_ratio = pad_image(img)
                    # get_features_from_image also takes a crop direction arguments in case you don't have square images
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
                            print("BBoxes for " + file_path)
                            print('Found %d bounding boxes (%d ms.)' % (len(res["result"]["bounding_boxes"]), res['timing']['dsp'] + res['timing']['classification']))
                        for bb in res["result"]["bounding_boxes"]:
                            if config_loader.get_value("DEBUG") == 1:
                                print('\t%s (%.2f): x=%d y=%d w=%d h=%d' % (bb['label'], bb['value'], bb['x'], bb['y'], bb['width'], bb['height']))
                            if bb['value'] > float(config_loader.get_value("DETECTION_THRESHOLD")):
                                if config_loader.get_value("DEBUG") == 1:
                                    print(f"Detection for {file_path}")
                                current_detection_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                        if (current_detection_time - last_detection_time).total_seconds() > detection_time_interval:
                            now = datetime.datetime.now()
                            if config_loader.get_value("DETECTION_UPLOADEDGE") == 1:
                                cv2.imwrite(os.path.join(config_loader.get_value("DATAFOLDER"), 'detected', f'{now.strftime("%Y%m%d%H%M%S%f")}.jpg'),  restore_image(cropped, aspect_ratio))
                            last_detection_time = current_detection_time
                            cropped = cv2.rectangle(cropped, (bb['x'], bb['y']), (bb['x'] + bb['width'], bb['y'] + bb['height']), (255, 0, 0), 1)
                            (text_width, text_height), _ = cv2.getTextSize(f"{bb['label']}: {bb['value']:.2f}", cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                            cropped = cv2.rectangle(cropped, (bb['x'], bb['y']-text_height - 5), (bb['x']+text_width, bb['y']), (255, 0, 0), -1)
                            cropped = cv2.putText(cropped, f"{bb['label']}: {bb['value']:.2f}", (bb['x'], bb['y'] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                            cv2.imwrite(os.path.join(config_loader.get_value("DATAFOLDER"), 'detectedTelegram', f'{now.strftime("%Y%m%d%H%M%S%f")}.jpg'),  restore_image(cropped, aspect_ratio))      
                    os.remove(file_path)
                time.sleep(5) 

        finally:
            if (runner):
                runner.stop()

if __name__ == "__main__":
   main(sys.argv[1:])
