import pandas as pd
import yfinance as yf
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
import datetime
import logging
import warnings

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

def fetch_exogenous_features(start_date, end_date):
    """
    Fetches external features like Crude Oil and USD/THB exchange rate from Yahoo Finance.
    """
    try:
        # CL=F is Crude Oil, THB=X is USD/THB
        tickers = ["CL=F", "THB=X"]
        df_ext = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
        
        # yfinance returns multi-index columns if multiple tickers are passed
        if isinstance(df_ext.columns, pd.MultiIndex):
            df_ext.columns = df_ext.columns.get_level_values(1)
            
        # Clean up column names and handle missing data
        df_ext = df_ext.rename(columns={"CL=F": "Crude_Oil", "THB=X": "USD_THB"})
        df_ext = df_ext.ffill().bfill() # Forward fill then backward fill for weekends/holidays
        return df_ext
    except Exception as e:
        logger.error(f"Error fetching exogenous features: {e}")
        return pd.DataFrame()

def generate_forecast(df: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """
    Generates a forecast for the next `days` using XGBoost and exogenous features.
    Expects df with a 'date' datetime index and a 'price' column.
    """
    if df.empty or len(df) < 14:
        logger.warning("Not enough data to forecast. Requires at least 14 days.")
        return pd.DataFrame()

    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    start_date = df.index.min().strftime('%Y-%m-%d')
    # Fetch end_date slightly in the future to ensure we have data for the forecast period (using last known values if needed)
    end_date_fetch = (df.index.max() + pd.Timedelta(days=days)).strftime('%Y-%m-%d')
    
    logger.info(f"Fetching exogenous features from {start_date} to {end_date_fetch}")
    df_ext = fetch_exogenous_features(start_date, end_date_fetch)
    
    if not df_ext.empty:
        # Localize df_ext timezone if it exists (yfinance sometimes returns timezone-aware)
        if df_ext.index.tz is not None:
             df_ext.index = df_ext.index.tz_localize(None)
        
        # Merge dataframes
        merged_df = df.join(df_ext, how='left')
        merged_df = merged_df.ffill().bfill()
        
        if 'Crude_Oil' in merged_df.columns and 'USD_THB' in merged_df.columns:
            logger.info("Using XGBoost with Exogenous Features.")
            
            # Prepare features for training
            merged_df['day_of_week'] = merged_df.index.dayofweek
            merged_df['day_of_month'] = merged_df.index.day
            
            # We want to predict the price, so we shift the price column to create a target
            # For a 1-day ahead forecast:
            merged_df['target'] = merged_df['price'].shift(-1)
            
            # For training, drop the na target rows
            train_df = merged_df.dropna(subset=['target'])
            
            features = ['price', 'Crude_Oil', 'USD_THB', 'day_of_week', 'day_of_month']
            X = train_df[features]
            y = train_df['target']
            
            model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
            model.fit(X, y)
            
            # Predict sequentially for 'days'
            forecast_dates = []
            forecast_prices = []
            
            current_features = merged_df.iloc[-1][features].copy()
            current_date = merged_df.index[-1]
            
            for i in range(1, days + 1):
                pred_date = current_date + pd.Timedelta(days=i)
                forecast_dates.append(pred_date)
                
                # Update time features
                current_features['day_of_week'] = pred_date.dayofweek
                current_features['day_of_month'] = pred_date.day
                
                # Exogenous features extrapolation (naive approach: carry forward last known)
                if pred_date in df_ext.index:
                    current_features['Crude_Oil'] = df_ext.loc[pred_date, 'Crude_Oil']
                    current_features['USD_THB'] = df_ext.loc[pred_date, 'USD_THB']
                
                # Predict
                X_pred = pd.DataFrame([current_features])
                pred_price = model.predict(X_pred)[0]
                forecast_prices.append(pred_price)
                
                # Update 'price' feature for the next iteration's prediction
                current_features['price'] = pred_price
                
            forecast_df = pd.DataFrame({
                'date': forecast_dates,
                'predicted_price': forecast_prices
            })
            forecast_df.set_index('date', inplace=True)
            return forecast_df
            
    logger.warning("Falling back to simple historical extrapolation (ARIMA logic from previous build).")
    # ... Fallback if yfinance fails
    from statsmodels.tsa.arima.model import ARIMA
    try:
        model = ARIMA(df['price'], order=(1, 1, 1))
        fitted = model.fit()
        forecast = fitted.forecast(steps=days)
        last_date = df.index[-1]
        forecast_dates = [last_date + pd.Timedelta(days=i) for i in range(1, days + 1)]
        forecast_df = pd.DataFrame({'date': forecast_dates, 'predicted_price': forecast.values})
        forecast_df.set_index('date', inplace=True)
        return forecast_df
    except Exception as e:
        logger.error(f"Error in fallback model: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
    prices = [60 + i*0.1 for i in range(30)]
    df = pd.DataFrame({'price': prices}, index=dates)
    forecast = generate_forecast(df, days=3)
    print(forecast)
