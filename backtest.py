import pandas as pd
import numpy as np
from database import get_session, LatexPrice
from advanced_forecasting import generate_forecast
import logging
import datetime
from sklearn.metrics import mean_absolute_error, mean_squared_error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_backtest(country, window_days=30):
    """
    Simulates historical forecasting to measure accuracy.
    Uses a rolling window approach.
    """
    session = get_session()
    try:
        # Fetch all historical data for the country
        history = session.query(LatexPrice).filter_by(country=country).order_by(LatexPrice.date.asc()).all()
        if len(history) < window_days + 5:
            logger.warning(f"Not enough data for {country} to run a meaningful backtest.")
            return None

        data = []
        for h in history:
            data.append({'date': pd.to_datetime(h.date), 'price': h.price})
            
        full_df = pd.DataFrame(data).set_index('date')
        
        results = []
        
        # We start forecasting from index 'window_days'
        # For each point, we use data[:i] to predict data[i]
        for i in range(window_days, len(full_df)):
            current_date = full_df.index[i]
            actual_price = full_df.iloc[i]['price']
            
            # Training data is everything before this date
            train_df = full_df.iloc[:i]
            
            # Generate 1-day forecast
            try:
                forecast_df = generate_forecast(train_df, days=1)
                if not forecast_df.empty:
                    predicted_price = forecast_df.iloc[0]['predicted_price']
                    
                    results.append({
                        'date': current_date,
                        'actual': actual_price,
                        'predicted': predicted_price,
                        'error': predicted_price - actual_price,
                        'abs_error': abs(predicted_price - actual_price)
                    })
            except Exception as e:
                logger.error(f"Error forecasting for {current_date}: {e}")
                continue
                
        if not results:
            return None
            
        res_df = pd.DataFrame(results)
        
        # Metrics
        mae = mean_absolute_error(res_df['actual'], res_df['predicted'])
        rmse = np.sqrt(mean_squared_error(res_df['actual'], res_df['predicted']))
        mape = np.mean(np.abs((res_df['actual'] - res_df['predicted']) / res_df['actual'])) * 100
        
        # Direction accuracy
        res_df['actual_diff'] = res_df['actual'].diff()
        # For the first row, we need the diff from the previous day in train_df
        res_df.iloc[0, res_df.columns.get_loc('actual_diff')] = res_df.iloc[0]['actual'] - full_df.iloc[window_days-1]['price']
        
        res_df['predicted_diff'] = res_df['predicted'] - full_df.shift(1).iloc[window_days:]['price'].values
        # Again, fix the first row
        res_df.iloc[0, res_df.columns.get_loc('predicted_diff')] = res_df.iloc[0]['predicted'] - full_df.iloc[window_days-1]['price']
        
        res_df['correct_direction'] = ((res_df['actual_diff'] > 0) == (res_df['predicted_diff'] > 0)) | \
                                      ((res_df['actual_diff'] < 0) == (res_df['predicted_diff'] < 0))
        
        dir_accuracy = res_df['correct_direction'].mean() * 100
        
        summary = {
            'country': country,
            'mae': mae,
            'rmse': rmse,
            'mape': f"{mape:.2f}%",
            'direction_accuracy': f"{dir_accuracy:.2f}%",
            'sample_size': len(res_df)
        }
        
        return summary, res_df

    finally:
        session.close()

if __name__ == "__main__":
    countries = ["Thailand", "India", "Malaysia", "China"]
    all_summaries = []
    
    print("\n--- Rubber Forecast Backtesting Report ---")
    for country in countries:
        result = run_backtest(country)
        if result:
            summary, _ = result
            all_summaries.append(summary)
            print(f"\nResults for {country}:")
            for k, v in summary.items():
                print(f"  {k.upper()}: {v}")
        else:
            print(f"\nSkipping {country}: Insufficient historical data.")
            
    if all_summaries:
        summary_df = pd.DataFrame(all_summaries)
        print("\nOverall Summary Table:")
        print(summary_df.to_string(index=False))
