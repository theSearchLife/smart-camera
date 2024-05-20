import os
import sys
import asyncio
from telegram import Bot, error
from datetime import datetime
import config_loader

async def send_photo_async(bot, channel_id, photo_path):
    try:
        await asyncio.sleep(1)  # Implementing delay between each message to prevent rate limiting
        photo_time = datetime.fromtimestamp(os.path.getmtime(photo_path)).strftime("%Y-%m-%d %H:%M:%S.%f")
        with open(photo_path, 'rb') as photo:
            media_type = photo_path.lower().split('.')[-1]
            if media_type == 'gif':
                await bot.send_animation(chat_id=channel_id, animation=photo, caption=f'Detection from camera with name {config_loader.get_value("CAPTURE_NAME")} at {photo_time}', read_timeout=5, write_timeout=20, connect_timeout=5, pool_timeout=5)
            elif media_type == 'mp4':
                await bot.send_video(chat_id=channel_id, video=photo, caption=f'Detection from camera with name {config_loader.get_value("CAPTURE_NAME")} at {photo_time}', read_timeout=5, write_timeout=20, connect_timeout=5, pool_timeout=5)
            elif media_type == 'jpg':
                await bot.send_photo(chat_id=channel_id, photo=photo, caption=f'Detection from camera with name {config_loader.get_value("CAPTURE_NAME")} at {photo_time}', read_timeout=5, write_timeout=20, connect_timeout=5, pool_timeout=5)
    except error.BadRequest as e:
        if "File must be non-empty" in str(e):
            print(f"Caught empty file error for {photo_path}. Retrying...")
            await asyncio.sleep(1)  # Delay to allow time for the file to be ready
            await send_photo_async(bot, channel_id, photo_path)  # Retry sending the photo
        else:
            raise
    except error.TimedOut as te:
        print(f"Timeout error: {te}. Retrying...")
        await asyncio.sleep(te.retry_after if hasattr(te, "retry_after") else 10)  # Wait before retrying
        await send_photo_async(bot, channel_id, photo_path)  # Retry sending the photo       
    except Exception as e:
        print(f"An error occurred: {e}")

async def process_files(bot, channel_id, dir_name):
    list_of_files = filter(lambda x: os.path.isfile(os.path.join(dir_name, x)), os.listdir(dir_name))
    list_of_files = sorted(list_of_files, key=lambda x: os.path.getmtime(os.path.join(dir_name, x)))
    for file in list_of_files:
        file_path = os.path.join(dir_name, file)
        await send_photo_async(bot, channel_id, file_path)
        os.remove(file_path)  # Be cautious with file deletion
        # await asyncio.sleep(1.5)  # Implementing delay between each message to prevent rate limiting

async def main(argv):
    config_loader.load_config(argv[0])
    TOKEN = config_loader.get_value("ALERT_TOKEN")
    channel_id = config_loader.get_value("ALERT_CHANNELID")
    bot = Bot(token=TOKEN)
    dir_name = config_loader.get_value("DATAFOLDER") + "/detectedTelegram/"
    while True:
        await process_files(bot, channel_id, dir_name)
        await asyncio.sleep(1)  # Delay before starting the loop again

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
