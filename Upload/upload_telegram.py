import os
import sys
import asyncio
from aiogram import Bot
from aiogram.types import FSInputFile
import config_loader

async def send_photo_async(bot, channel_id, photo_path):
    try:
        await bot.send_photo(chat_id=channel_id, photo=FSInputFile(photo_path), caption=f'Detection from camera with name {config_loader.get_value("CAPTURE_NAME")}')
    except Exception as ex:
        print(f"An error occurred: {ex}")
        # Sleep to avoid flooding the API with requests when an error occurs
        await asyncio.sleep(ex.retry_after if hasattr(ex, "retry_after") else 10)
        # Retry sending the photo
        await bot.send_photo(chat_id=channel_id, photo=FSInputFile(photo_path), caption=f'Detection from camera with name {config_loader.get_value("CAPTURE_NAME")}')

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
        await asyncio.sleep(0.5)  # Delay before starting the loop again

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
