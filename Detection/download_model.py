import os
import sys
import time
import shutil
import subprocess
import config_loader

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

def clear_directory_contents(path):
    """Remove all contents of a directory but keep the directory itself."""
    if os.path.exists(path):
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                print(f"Removed: {file_path}")
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    else:
        print(f"Directory not found: {path}")

def main():
    directories_to_clear = [
        "Data/debug",
        "Data/detected",
        "Data/detectedTelegram"
    ]
    while True:
        for directory in directories_to_clear:
            clear_directory_contents(directory)
        print("Downloading the model...")
        download_model()
        print("Download completed. Waiting 24 hours for the next download.")
        time.sleep(86400)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        print("Error: Please provide the configuration file as an argument.", file=sys.stderr)
