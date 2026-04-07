# 🌿 Rubber Market Intelligence & Forecasting

A production-grade, automated pipeline for global natural rubber (latex) price tracking, sentiment analysis, and AI-driven forecasting. This project moves beyond simple monitoring by integrating **XGBoost machine learning**, **FinBERT financial NLP**, and **real-time weather correlation** to provide actionable market insights.

---

## 🚀 "Level Up" Features

| Phase | Feature | Details |
|---|---|---|
| 🌐 **Data** | **Real-World Scrapers** | Live data for **Thailand**, **India**, **Malaysia**, and **China** with resilient news-extraction fallbacks. |
| 🧠 **Intelligence** | **FinBERT Sentiment** | Advanced financial sentiment analysis using **ProsusAI/FinBERT** (Hugging Face) for market-aware NLP. |
| 🌦️ **Forecasting** | **Weather Correlation** | XGBoost model enhanced with **Rainfall data** from major producing regions via Open-Meteo. |
| 📊 **Interface** | **Streamlit Dashboard** | **New Interactive Web UI** with Plotly charts for deep-dive historical analysis. |
| 🧪 **Quality** | **Backtesting & Tests** | Built-in framework to measure forecast accuracy (MAE/RMSE) and automated `pytest` suite. |

---

## 🏗️ Architecture

```
main.py (orchestrator)
├── data_fetcher.py       → Scrapers for TH, IN, MY, CN + News Fallback
├── dashboard.py          → Streamlit Web Dashboard (Interactive Plotly UI)
├── sentiment_analysis.py → Google News RSS + FinBERT (Transformers)
├── advanced_forecasting.py → XGBoost + Oil (yfinance) + Rain (Open-Meteo)
├── backtest.py           → Accuracy measurement framework (MAE/RMSE)
├── database.py           → SQLite schema (SQLAlchemy) + .env support
├── tests/                → Automated pytest suite (Normalization, Schema)
└── notifier.py           → Telegram Bot (Sync/Async support)
```

---

## ⚙️ Setup & Usage

### 1. Install & Configure
```bash
git clone https://github.com/yourusername/rubber.git
cd rubber
pip install -r requirements.txt
cp .env.example .env  # Update with your Telegram tokens
```

### 2. Launch the Dashboard
Experience the data interactively:
```bash
streamlit run dashboard.py
```

### 3. Run a Backtest
Verify the model's historical accuracy:
```bash
python backtest.py
```

### 4. Run Daily Job
Manual run with Telegram notification:
```bash
python main.py --run-now
```

---

## 📊 AI Forecasting Model
The **XGBoost Regressor** now utilizes:
1. **Historical Lag Features:** Previous price trends.
2. **Financial Exogenous:** Crude Oil (`CL=F`) and FX (`THB=X`).
3. **Weather Exogenous:** Daily precipitation sum from **Songkhla, Thailand**.
4. **Time Features:** Day of week/month seasonality.

---

## 📰 Financial Sentiment (FinBERT)
Unlike general NLP, our integration uses **FinBERT**, which understands financial context (e.g., "Market pressure" is correctly identified as Bearish). It processes the top 10 global headlines daily to provide a weighted market sentiment score.

---

## 📁 Project Structure
- `dashboard.py`: Interactive Streamlit application.
- `backtest.py`: Forecast accuracy reporting tool.
- `.env.example`: Template for environment variables.
- `tests/`: Directory for `pytest` unit and integration tests.
- `charts/`: Generated static charts for Telegram reports.

---

## 📄 License
MIT License.
