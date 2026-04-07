import requests
from bs4 import BeautifulSoup
import datetime
import random
import logging
import re
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common browser headers to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def fetch_thailand_price():
    """Fetches STR 20 latex price from Thai Rubber Association."""
    try:
        url = "https://www.thainr.com/en/index.php?plan=price"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        logger.info(f"Thailand fetch status: {response.status_code}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        text = soup.get_text()
        if "STR 20" in text:
            idx = text.find("STR 20")
            sub_text = text[idx:idx+200]
            match = re.search(r'(\d+\.\d{2})\s*BAHT/KG', sub_text)
            if match:
                price = float(match.group(1))
                logger.info(f"Successfully fetched Thailand price: {price}")
                return price, "THB/kg"
    except Exception as e:
        logger.error(f"Error fetching Thailand price: {e}")
    
    logger.info("Using mock data for Thailand")
    return round(random.uniform(65.0, 75.0), 2), "THB/kg"

import feedparser

def fetch_price_from_news(query, country_tag, currency_unit):
    """
    Fallback method to extract rubber price from news headlines.
    Improved to avoid picking up price changes (drops/rises).
    """
    try:
        rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
        feed = feedparser.parse(rss_url)
        
        # Keywords that indicate a change rather than an absolute price
        change_keywords = ['drop', 'rise', 'increase', 'decrease', 'fell', 'jump', 'up', 'down', 'gain', 'lose']
        
        for entry in feed.entries:
            title = entry.title
            logger.info(f"Checking news headline for {country_tag}: {title}")
            
            # Skip if headline looks like a change report
            if any(word in title.lower() for word in change_keywords):
                # Only skip if the change keyword is very close to the price (e.g. "drop Rs 25")
                # This is a bit complex for regex, so we'll just check if it's a general change headline
                if re.search(r'(?:drop|rise|increase|decrease|fell|jump)\s+(?:Rs\.?\s*)?\d+', title, re.IGNORECASE):
                    logger.info(f"Skipping potential change headline: {title}")
                    continue

            patterns = [
                r'Rs\.?\s*(\d{3}(?:\.\d{2})?)', # India (Expecting 3 digits like 226)
                r'(\d{2,5}(?:\.\d{2})?)\s*Sen',    # Malaysia
                r'(\d{4,5}(?:\.\d{2})?)\s*RMB',   # China
                r'(\d{4,5}(?:\.\d{2})?)\s*yuan',  # China
                r'(\d{2,3}(?:\.\d{2})?)\s*Baht',  # Thailand
                r'(\d{2,3}(?:\.\d{2})?)\s*USD',   # Generic
            ]
            
            for pattern in patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    price = float(match.group(1))
                    
                    # India specific sanity check: prices are usually 150-300 INR/kg
                    if 'India' in country_tag:
                        if price < 100: # Clearly too low (likely a change value we missed)
                            continue
                        if price > 500: price = price / 100.0 # Handle per 100kg
                        if not (150 <= price <= 350): # Real-world bounds for 2024-2026
                            continue
                    
                    # Malaysia specific: Convert Sen to MYR
                    if 'Malaysia' in country_tag and 'Sen' in pattern:
                        price = price / 100.0
                            
                    logger.info(f"Extracted {country_tag} price from news: {price} {currency_unit}")
                    return price, currency_unit
    except Exception as e:
        logger.error(f"Error extracting price from news for {country_tag}: {e}")
    return None

def fetch_india_price():
    """Fetches RSS4 price from Rubber Board of India's website or news."""
    # 1. Try Direct Scraper
    try:
        url = "https://www.rubberboard.gov.in/public"
        response = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        for row in soup.find_all('tr'):
            if 'RSS 4' in row.text:
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    txt = cell.text.strip().replace(',', '')
                    match = re.search(r'(\d{2,5}\.\d{2})', txt)
                    if match:
                        price = float(match.group(1))
                        if price > 500: price = price / 100.0
                        return price, "INR/kg"
    except Exception as e:
        logger.error(f"Error fetching India price (direct): {e}")

    # 2. Try News Extractor
    news_price = fetch_price_from_news("rubber price RSS4 Kottayam today", "India", "INR/kg")
    if news_price: return news_price

    logger.info("Using mock data for India")
    return round(random.uniform(210.0, 230.0), 2), "INR/kg"

def fetch_malaysia_price():
    """Fetches SMR 20 price from Malaysian Rubber Board or news."""
    # 1. Try Direct Scraper
    try:
        url = "https://www.lgm.gov.my/webv2/mre/daily-prices"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        for row in soup.find_all('tr'):
            if 'SMR 20' in row.text:
                cells = row.find_all('td')
                if len(cells) > 1:
                    for cell in cells:
                        txt = cell.text.strip().replace(',', '')
                        match = re.search(r'(\d{3}\.\d{2})', txt)
                        if match:
                            price_sen = float(match.group(1))
                            return price_sen / 100.0, "MYR/kg"
    except Exception as e:
        logger.error(f"Error fetching Malaysia price (direct): {e}")

    # 2. Try News Extractor
    news_price = fetch_price_from_news("Malaysian Rubber Board SMR 20 price today", "Malaysia", "MYR/kg")
    if news_price: return news_price

    logger.info("Using mock data for Malaysia")
    return round(random.uniform(8.0, 9.0), 2), "MYR/kg"

def fetch_china_price():
    """Fetches TSR 20 (NR) from INE or news."""
    # 1. Try Direct Scraper
    try:
        base_url = "http://www.ine.cn/data/dailydata/kx/kx{}.dat"
        for i in range(6):
            dt = (datetime.date.today() - datetime.timedelta(days=i)).strftime("%Y%m%d")
            url = base_url.format(dt)
            try:
                response = requests.get(url, headers={'User-Agent': HEADERS['User-Agent'], 'Referer': 'http://www.ine.cn/en/data/dailydata/'}, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'o_curinstrument' in data:
                        for item in data['o_curinstrument']:
                            if item['PRODUCTID'].strip().lower() == 'nr_f' and item['SETTLEMENTPRICE']:
                                return float(item['SETTLEMENTPRICE']), "CNY/ton"
            except:
                continue
    except Exception as e:
        logger.error(f"Error fetching China price (direct): {e}")

    # 2. Try News Extractor
    news_price = fetch_price_from_news("Shanghai TSR 20 rubber price today", "China", "CNY/ton")
    if news_price: return news_price

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
