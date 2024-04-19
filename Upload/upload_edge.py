import os
import time
import sys
import config_loader


def main(argv):
    time.sleep(20)
    try:
        config_loader.load_config(argv[0])
        while True:
            try:
                os.system(f'edge-impulse-uploader --api-key {config_loader.get_value("DETECTION_APIKEY")} {os.path.join(config_loader.get_value("DATAFOLDER"), "detected/*.jpg")}')
            except Exception as ex:
                print(ex)

            import glob
            removing_files = glob.glob(config_loader.get_value("DATAFOLDER") +"/detected/*.jpg")
            for i in removing_files:
                os.remove(i)
            print("done")
            time.sleep(100)
    except Exception as ex:
        print(ex)

if __name__ == "__main__":
   main(sys.argv[1:])