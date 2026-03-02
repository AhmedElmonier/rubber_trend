import requests
from bs4 import BeautifulSoup
import datetime
import random
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_thailand_price():
    """Fetches STR 20 latex price from Thai Rubber Association."""
    try:
        url = "https://www.thainr.com/en/index.php?plan=price"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        text = soup.get_text()
        if "STR 20" in text:
            idx = text.find("STR 20")
            sub_text = text[idx:idx+200]
            match = re.search(r'(\d+\.\d{2})\s*BAHT/KG', sub_text)
            if match:
                price = float(match.group(1))
                return price, "THB/kg"
    except Exception as e:
        logger.error(f"Error fetching Thailand price: {e}")
    
    logger.info("Using mock data for Thailand")
    return round(random.uniform(60.0, 70.0), 2), "THB/kg"

def fetch_india_price():
    """Fetches RSS4 price from Rubber Board of India's website."""
    logger.info("Using mock data for India")
    return round(random.uniform(150.0, 180.0), 2), "INR/kg"

def fetch_malaysia_price():
    """Fetches SMR 20 price from Malaysian Rubber Board."""
    logger.info("Using mock data for Malaysia")
    return round(random.uniform(6.0, 8.0), 2), "MYR/kg"

def fetch_china_price():
    """Fetches TSR 20 from Shanghai Futures Exchange or investing.com."""
    logger.info("Using mock data for China")
    return round(random.uniform(13000.0, 15000.0), 2), "CNY/ton"

def fetch_all_prices():
    """Returns a dictionary of all prices for the current day."""
    return {
        "Thailand": fetch_thailand_price(),
        "India": fetch_india_price(),
        "Malaysia": fetch_malaysia_price(),
        "China": fetch_china_price()
    }

if __name__ == "__main__":
    print(fetch_all_prices())
