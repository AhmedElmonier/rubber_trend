import os
import telegram
from dotenv import load_dotenv
import logging
import asyncio

load_dotenv()
logger = logging.getLogger(__name__)

bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

async def send_telegram_message(text: str, image_paths: list = None):
    """
    Sends a message and optional images to a Telegram chat.
    Splits text if it's too long for a caption (1024 limit).
    """
    if not bot_token or not chat_id or bot_token == 'your_token_here':
        logger.warning("Telegram bot token or chat ID is not valid. Skipping notification.")
        print(f"--- MOCK NOTIFICATION ---\n{text}\nImages: {image_paths}\n-----------------------")
        return

    bot = telegram.Bot(token=bot_token)
    
    try:
        # 1. If images exist, check caption length
        if image_paths:
            if len(text) > 1000: # Safe margin below 1024
                # Send text first, then images
                await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
                media = [telegram.InputMediaPhoto(open(p, 'rb')) for p in image_paths]
                await bot.send_media_group(chat_id=chat_id, media=media)
            else:
                # Send together
                if len(image_paths) == 1:
                    with open(image_paths[0], 'rb') as photo:
                        await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, parse_mode='Markdown')
                else:
                    media = []
                    for idx, path in enumerate(image_paths):
                        caption = text if idx == 0 else ''
                        media.append(telegram.InputMediaPhoto(open(path, 'rb'), caption=caption, parse_mode='Markdown'))
                    await bot.send_media_group(chat_id=chat_id, media=media)
        else:
            # 2. No images, just send text
            await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
            
        logger.info("Telegram notification sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")

def notify_sync(text: str, image_paths: list = None):
    """Synchronous wrapper for sending telegram messages."""
    asyncio.run(send_telegram_message(text, image_paths))
