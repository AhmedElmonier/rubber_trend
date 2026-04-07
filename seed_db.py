import pandas as pd
import datetime
import random
from database import get_session, LatexPrice, init_db

def seed_database():
    init_db()
    session = get_session()
    
    countries = {
        "Thailand": (60.0, 70.0, "THB/kg"),
        "India": (150.0, 180.0, "INR/kg"),
        "Malaysia": (6.0, 8.0, "MYR/kg"),
        "China": (13000.0, 15000.0, "CNY/ton")
    }
    
    today = datetime.date.today()
    
    for country, (low, high, unit) in countries.items():
        base_price = random.uniform(low, high)
        for i in range(60, 0, -1):
            past_date = today - datetime.timedelta(days=i)
            # Add proportional random walk for realism (e.g., +/- 1.5% daily change)
            change_pct = random.uniform(-0.015, 0.015)
            base_price = base_price * (1 + change_pct)
            
            if base_price < low * 0.8: base_price = low * 0.8 # keep it somewhat bound
            
            # check if exists
            exists = session.query(LatexPrice).filter_by(date=past_date, country=country).first()
            if not exists:
                record = LatexPrice(
                    date=past_date,
                    country=country,
                    price=round(base_price, 2),
                    currency_unit=unit
                )
                session.add(record)
    
    session.commit()
    session.close()
    print("Database seeded with 60 days of mock historical data.")

if __name__ == "__main__":
    seed_database()
