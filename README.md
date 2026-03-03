# 🌿 Latex Price Forecaster & Notifier

An automated Python pipeline that tracks daily natural rubber/latex prices across **Thailand, India, Malaysia, and China**. It applies **XGBoost machine learning** fused with real-time exogenous market data (Crude Oil prices, USD exchange rates) to produce 7-day price forecasts, performs **NLP sentiment analysis** on live rubber market news, and delivers a complete daily report with matplotlib charts via a **Telegram Bot** — all automated through **GitHub Actions**.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🌐 **Web Scraping** | Scrapes live STR 20 prices from the Thai Rubber Association (thainr.com); mock fallback data for India, Malaysia & China |
| 🤖 **XGBoost Forecasting** | Predicts 7-day price trends using a trained XGBoost model with lag features + exogenous signals |
| 📈 **Exogenous Features** | Fetches real-time Crude Oil (`CL=F`) and USD/THB (`THB=X`) rates from Yahoo Finance via `yfinance` |
| 📉 **ARIMA Fallback** | Automatically falls back to ARIMA(1,1,1) if `yfinance` data is unavailable |
| 📰 **Sentiment Analysis** | Analyzes top Google News RSS headlines using **TextBlob** NLP; reports Bullish/Neutral/Bearish signals |
| 💬 **Telegram Reporting** | Sends daily price reports + 4 country-specific forecast charts as a media group |
| 🗄️ **SQLite Database** | Persists all historical prices locally; auto-seeded with mock history on first run |
| 📊 **Matplotlib Charting** | Generates country price charts overlaying historical data with the 7-day forecast line |
| ⚙️ **GitHub Actions CI/CD** | Runs automatically every day at 09:00 UTC via a scheduled workflow; also supports manual dispatch |

---

## 🏗️ Architecture

```
main.py (orchestrator)
├── data_fetcher.py       → Scrapes / fetches live prices for 4 countries
├── database.py           → SQLite schema (SQLAlchemy ORM), init & session helpers
├── seed_db.py            → One-time mock historical data seeder
├── advanced_forecasting.py → XGBoost model + yfinance exogenous features; ARIMA fallback
├── charting.py           → Matplotlib line charts (history + forecast overlay)
├── sentiment_analysis.py → Google News RSS + TextBlob sentiment scoring
└── notifier.py           → Async Telegram Bot sender (text + image media group)

.github/workflows/
└── daily_report.yml      → Scheduled GitHub Actions workflow (cron: 0 9 * * *)
```

---

## ⚙️ Setup

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/rubber.git
cd rubber
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

> **For GitHub Actions:** Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as **Repository Secrets** under *Settings → Secrets and variables → Actions*.

---

## 🚀 Usage

### Seed the database (first run only)
Populates the SQLite DB with mock historical price data so the ML model has enough rows to train on:
```bash
python seed_db.py
```

### Run the full pipeline once
```bash
python main.py --run-now
```

### Run as a local daily scheduler
```bash
python main.py
```
> Keeps running in the terminal and fires the job every day at **09:00 AM local time**.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `requests` / `beautifulsoup4` / `lxml` | Web scraping (Thai Rubber Association) |
| `yfinance` | Fetching Crude Oil & FX rate data |
| `xgboost` / `scikit-learn` | XGBoost forecasting model |
| `statsmodels` | ARIMA fallback model |
| `pandas` / `matplotlib` | Data processing & chart generation |
| `feedparser` / `textblob` | Google News RSS + NLP sentiment |
| `python-telegram-bot` | Async Telegram Bot API |
| `sqlalchemy` | SQLite ORM |
| `schedule` | Local cron-style scheduler |
| `python-dotenv` | `.env` file loader |

---

## 🔄 GitHub Actions Workflow

The workflow file `.github/workflows/daily_report.yml` triggers at **09:00 UTC daily** and can also be run manually from the *Actions* tab.

**Steps:**
1. Checkout repository
2. Set up Python 3.10
3. Install dependencies from `requirements.txt`
4. Run `python main.py --run-now` with Telegram secrets injected

> **Note:** The SQLite database is not persisted between workflow runs. The pipeline auto-seeds mock history data when it detects an empty database, ensuring sufficient data for the XGBoost model on every run.

---

## 📋 Sample Telegram Report

```
🌿 Latex Prices for 2026-03-03

- Thailand: 65.20 THB/kg (~$1.84 USD/kg) [+0.50 THB/kg, +0.77%]
- India: 162.40 INR/kg (~$1.96 USD/kg)
- Malaysia: 6.85 MYR/kg (~$1.46 USD/kg)
- China: 13800.00 CNY/ton (~$1.92 USD/kg)

📈 Next Day Forecast Predictions
- Thailand: 65.74 THB/kg (~$1.85 USD/kg)
- India: 163.10 INR/kg (~$1.97 USD/kg)
- ...

📰 Market Sentiment Context
Overall: Bullish ⭐ (Score: 0.18)
- Rubber prices rise on supply concerns (Score: 0.35)
- ...
```

---

## 📁 Project Structure

```
rubber/
├── .env                      # Local secrets (not committed)
├── .github/workflows/        # GitHub Actions CI/CD
├── main.py                   # Main orchestrator
├── data_fetcher.py           # Price scraping & mock data
├── database.py               # SQLAlchemy models & DB helpers
├── seed_db.py                # Historical data seeder
├── advanced_forecasting.py   # XGBoost + ARIMA forecasting
├── charting.py               # Matplotlib chart generation
├── sentiment_analysis.py     # News RSS + TextBlob sentiment
├── notifier.py               # Telegram Bot notifier
├── requirements.txt          # Python dependencies
├── latex_prices.db           # Local SQLite database
└── charts/                   # Generated chart images
```

---

## 📄 License

MIT License — feel free to fork and adapt.
