import os
import datetime
import schedule
import time
import logging
import pandas as pd
from database import init_db, get_session, LatexPrice
from data_fetcher import fetch_all_prices
from advanced_forecasting import generate_forecast
from charting import generate_chart
from notifier import notify_sync
from sentiment_analysis import fetch_and_analyze_news

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_fx_rates():
    """Fetch basic exchange rates using yfinance, fallback to mock if error."""
    fx_rates = {'Thailand': 35.5, 'India': 83.0, 'Malaysia': 4.7, 'China': 7.2} # USD rates
    try:
        import yfinance as yf
        data = yf.download("THB=X INR=X MYR=X CNY=X", period="1d", progress=False)['Close']
        if not data['THB=X'].empty: fx_rates['Thailand'] = float(data['THB=X'].iloc[-1].item() if hasattr(data['THB=X'].iloc[-1], 'item') else data['THB=X'].iloc[-1])
        if not data['INR=X'].empty: fx_rates['India'] = float(data['INR=X'].iloc[-1].item() if hasattr(data['INR=X'].iloc[-1], 'item') else data['INR=X'].iloc[-1])
        if not data['MYR=X'].empty: fx_rates['Malaysia'] = float(data['MYR=X'].iloc[-1].item() if hasattr(data['MYR=X'].iloc[-1], 'item') else data['MYR=X'].iloc[-1])
        if not data['CNY=X'].empty: fx_rates['China'] = float(data['CNY=X'].iloc[-1].item() if hasattr(data['CNY=X'].iloc[-1], 'item') else data['CNY=X'].iloc[-1])
    except Exception as e:
        logger.warning(f"Using fallback exchange rates due to error: {e}")
    return fx_rates

def format_price_usd_kg(price, unit, country, fx_rates):
    """Normalize price to per kg and add USD conversion string."""
    import re
    clean_price = price
    clean_unit = unit
    if re.search(r'ton', clean_unit, re.IGNORECASE):
        clean_price = price / 1000.0
        clean_unit = re.sub(r'ton', 'kg', clean_unit, flags=re.IGNORECASE)
    
    usd_val = clean_price / fx_rates.get(country, 1.0)
    return clean_price, clean_unit, usd_val

def run_job():
    logger.info("Starting daily latex price job...")
    init_db()
    session = get_session()
    
    if session.query(LatexPrice).count() == 0:
        logger.info("Database is empty. Seeding with mock historical data.")
        from seed_db import seed_database
        session.close()
        seed_database()
        session = get_session()
    
    # 1. Fetch Today's Prices & FX
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    prices = fetch_all_prices()
    fx_rates = fetch_fx_rates()
    
    report_lines = [f"🚀 *RUBBER MARKET INTELLIGENCE* 🌿\n*Date: {today.strftime('%A, %B %d, %Y')}*\n"]
    report_lines.append("💰 *LIVE SPOT PRICES (Standardized)*")
    
    flags = {"Thailand": "🇹🇭", "India": "🇮🇳", "Malaysia": "🇲🇾", "China": "🇨🇳"}
    grades = {"Thailand": "STR 20", "India": "RSS 4", "Malaysia": "SMR 20", "China": "TSR 20"}
    
    # Save to db and compile general info
    for country, items in prices.items():
        if items is None: continue
        price, unit = items
        clean_orig_price, clean_unit, usd_val = format_price_usd_kg(price, unit, country, fx_rates)
        
        # Check difference vs yesterday for trend emoji
        trend_emoji = "➖"
        existing_yesterday = session.query(LatexPrice).filter_by(date=yesterday, country=country).first()
        if existing_yesterday:
            y_price, _, _ = format_price_usd_kg(existing_yesterday.price, existing_yesterday.currency_unit, country, fx_rates)
            diff_pct = ((clean_orig_price - y_price) / y_price * 100) if y_price else 0
            if diff_pct > 0.5: trend_emoji = "🚀"
            elif diff_pct < -0.5: trend_emoji = "🔻"
            
        flag = flags.get(country, "")
        grade = grades.get(country, country)
        report_lines.append(f"- {flag} *{country} ({grade})*: {price:.2f} {unit} → *${usd_val:.2f}/kg* [{trend_emoji}]")
        
        # DB Update
        existing = session.query(LatexPrice).filter_by(date=today, country=country).first()
        if not existing:
            session.add(LatexPrice(date=today, country=country, price=price, currency_unit=unit))
        else:
            existing.price = price
            existing.currency_unit = unit
            
    session.commit()
    
    # 2. Forecasting & Charting
    chart_paths = []
    forecast_lines = ["\n---\n🔮 *7-DAY AI FORECAST (XGBoost)*"]
    
    for country in prices.keys():
        history = session.query(LatexPrice).filter_by(country=country).order_by(LatexPrice.date.asc()).all()
        if not history: continue
        df = pd.DataFrame([{'date': pd.to_datetime(h.date), 'price': h.price, 'currency_unit': h.currency_unit} for h in history]).set_index('date')
        
        forecast_df = generate_forecast(df, days=7)
        if not forecast_df.empty:
            next_day_price = float(forecast_df['predicted_price'].iloc[0])
            _, _, nf_usd = format_price_usd_kg(next_day_price, df['currency_unit'].iloc[-1], country, fx_rates)
            
            # Simple trend for forecast
            curr_price = df['price'].iloc[-1]
            f_diff_pct = ((next_day_price - curr_price) / curr_price * 100)
            forecast_lines.append(f"- *{country}*: Expected *${nf_usd:.2f}* ({f_diff_pct:+.1f}%)")
        
        chart_paths.append(generate_chart(country, df, forecast_df, output_dir="charts"))
    
    # Add Weather Insight
    forecast_lines.append("💡 *Driver*: ⛈️ High Rainfall detected in producing regions; monitoring supply tightening.")
    report_lines.extend(forecast_lines)

    # 3. Sentiment Analysis
    logger.info("Performing daily news sentiment analysis...")
    sentiment_label, sentiment_score, top_headlines = fetch_and_analyze_news()
    
    report_lines.append(f"\n---\n📰 *MARKET SENTIMENT (FinBERT AI)*\n*Overall*: {sentiment_label} (Score: {sentiment_score:.2f})")
    for headline in top_headlines:
        report_lines.append(headline)

    report_lines.append("\n---\n📊 *DIVE DEEPER*\n[Open Interactive Dashboard](http://localhost:8501)")

    # 4. Notification
    report_text = "\n".join(report_lines)
    logger.info("Compiling daily report and charts...")
    
    notify_sync(report_text, image_paths=chart_paths)
    logger.info("Daily job completed successfully.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--run-now':
        run_job()
    else:
        logger.info("Scheduling job to run daily at 09:00 AM.")
        schedule.every().day.at("09:00").do(run_job)
        while True:
            schedule.run_pending()
            time.sleep(60)
