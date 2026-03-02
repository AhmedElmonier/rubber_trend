# Latex Price Forecaster & Notifier

An automated Python application that fetches daily latex prices from Thailand, India, Malaysia, and China. It utilizes advanced machine learning (XGBoost) combined with exogenous features (Crude Oil, USD Exchange Rates) to predict the next 7 days of price movement. It also performs NLP sentiment analysis on daily news and sends a comprehensive report with charts to Telegram.

## Features
- **Web Scraping**: Extracts daily STR20 prices from the Thai Rubber Association.
- **XGBoost Forecasting**: Predicts 7-day future trends using historical data + yfinance futures.
- **Sentiment Analysis**: Analyzes Google News RSS feeds using TextBlob to score market sentiment.
- **Automated Reporting**: Sends daily messages and matplotlib charts via a Telegram Bot.
- **Serverless CI/CD**: Runs automatically every day via GitHub Actions.

## Setup Instructions

1. **Clone the repository**
2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Variables:**
   Create a `.env` file in the root directory (or if using GitHub Actions, set up Repository Secrets):
   ```
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

## Usage

**Seed Database with Mock History (First Run Only):**
```bash
python seed_db.py
```

**Run End-to-End Pipeline Once:**
```bash
python main.py --run-now
```

**Run Local Scheduler:**
```bash
python main.py
```

*(Leave running in a terminal, it will execute daily at 09:00 AM)*
