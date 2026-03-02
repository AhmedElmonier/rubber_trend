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
    """
    if not bot_token or not chat_id or bot_token == 'your_token_here':
        logger.warning("Telegram bot token or chat ID is not valid. Skipping notification.")
        # Print it as a fallback for the console user
        print(f"--- MOCK NOTIFICATION ---\n{text}\nImages: {image_paths}\n-----------------------")
        return

    bot = telegram.Bot(token=bot_token)
    
    try:
        if image_paths:
            # Send media group if multiple images, or single photo
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
            await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
        logger.info("Telegram notification sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")

def notify_sync(text: str, image_paths: list = None):
    """Synchronous wrapper for sending telegram messages."""
    asyncio.run(send_telegram_message(text, image_paths))
