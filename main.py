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

def run_job():
    logger.info("Starting daily latex price job...")
    init_db()
    session = get_session()
    
    # 1. Fetch Today's Prices
    today = datetime.date.today()
    prices = fetch_all_prices()
    
    report_lines = [f"*Latex Prices for {today}*"]
    
    # Save to db
    for country, items in prices.items():
        if items is None:
            continue
        price, unit = items
        report_lines.append(f"- *{country}*: {price} {unit}")
        
        existing = session.query(LatexPrice).filter_by(date=today, country=country).first()
        if not existing:
            new_record = LatexPrice(date=today, country=country, price=price, currency_unit=unit)
            session.add(new_record)
        else:
            existing.price = price
            existing.currency_unit = unit
            
    session.commit()
    
    # 2. Forecasting & Charting
    chart_paths = []
    
    for country in prices.keys():
        history = session.query(LatexPrice).filter_by(country=country).order_by(LatexPrice.date.asc()).all()
        if not history:
            continue
            
        data = []
        for h in history:
            data.append({'date': pd.to_datetime(h.date), 'price': h.price, 'currency_unit': h.currency_unit})
            
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        
        forecast_df = generate_forecast(df, days=7)
        
        chart_path = generate_chart(country, df, forecast_df, output_dir="charts")
        chart_paths.append(chart_path)
    
    session.close()

    # 3. Sentiment Analysis
    logger.info("Performing daily news sentiment analysis...")
    sentiment_label, sentiment_score, top_headlines = fetch_and_analyze_news()
    
    report_lines.append("\n*Market Sentiment Context*")
    report_lines.append(f"Overall: {sentiment_label} (Score: {sentiment_score:.2f})")
    for headline in top_headlines:
        report_lines.append(headline)

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
