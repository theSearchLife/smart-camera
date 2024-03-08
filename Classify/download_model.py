import os
import sys
import time
import config_loader
import subprocess

def download_model():
    config_loader.load_config(sys.argv[1])
    model_name = config_loader.get_value("DETECTION_NETWORK")
    api_key = config_loader.get_value("DETECTION_APIKEY")
    command = f'edge-impulse-linux-runner --download {model_name} --api-key {api_key}'
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error occurred: {result.stderr}", file=sys.stderr)
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}.", file=sys.stderr)
    else:
        print(f"Model {model_name} downloaded or updated at {time.ctime()}.")

def main():
    while True:
        print("Downloading the model...")
        download_model()
        print("Download completed. Waiting 24 hours for the next download.")
        time.sleep(86400)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        print("Error: Please provide the configuration file as an argument.", file=sys.stderr)
