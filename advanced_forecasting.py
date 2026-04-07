import pandas as pd
import yfinance as yf
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
import datetime
import logging
import warnings
import requests

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

def fetch_rainfall(start_date, end_date):
    """
    Fetches historical rainfall data for Songkhla, Thailand (major rubber region) from Open-Meteo.
    """
    try:
        # Songkhla coordinates: 7.18, 100.59
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude=7.18&longitude=100.59&start_date={start_date}&end_date={end_date}&daily=precipitation_sum&timezone=Asia%2FBangkok"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            df_rain = pd.DataFrame({
                'date': pd.to_datetime(data['daily']['time']),
                'Rainfall': data['daily']['precipitation_sum']
            }).set_index('date')
            return df_rain
    except Exception as e:
        logger.error(f"Error fetching rainfall: {e}")
    return pd.DataFrame()

def fetch_exogenous_features(start_date, end_date):
    """
    Fetches external features: Crude Oil, USD/THB, and Rainfall.
    """
    try:
        # 1. Financial Features
        tickers = ["CL=F", "THB=X"]
        df_ext = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
        if isinstance(df_ext.columns, pd.MultiIndex):
            df_ext.columns = df_ext.columns.get_level_values(1)
        df_ext = df_ext.rename(columns={"CL=F": "Crude_Oil", "THB=X": "USD_THB"})
        
        # 2. Weather Feature (New)
        df_rain = fetch_rainfall(start_date, end_date)
        
        # Merge
        if not df_rain.empty:
            df_ext = df_ext.join(df_rain, how='outer')
            
        df_ext = df_ext.ffill().bfill()
        return df_ext
    except Exception as e:
        logger.error(f"Error fetching exogenous features: {e}")
        return pd.DataFrame()

def generate_forecast(df: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """
    Generates a forecast for the next `days` using XGBoost and exogenous features (Oil, FX, Rain).
    """
    if df.empty or len(df) < 14:
        logger.warning("Not enough data to forecast. Requires at least 14 days.")
        return pd.DataFrame()

    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    start_date = df.index.min().strftime('%Y-%m-%d')
    end_date_fetch = (df.index.max() + pd.Timedelta(days=days)).strftime('%Y-%m-%d')
    
    logger.info(f"Fetching exogenous features (Oil, FX, Rain) from {start_date} to {end_date_fetch}")
    df_ext = fetch_exogenous_features(start_date, end_date_fetch)
    
    if not df_ext.empty:
        if df_ext.index.tz is not None:
             df_ext.index = df_ext.index.tz_localize(None)
        
        merged_df = df.join(df_ext, how='left')
        merged_df = merged_df.ffill().bfill()
        
        # Define features to use
        features = ['price', 'day_of_week', 'day_of_month']
        if 'Crude_Oil' in merged_df.columns: features.append('Crude_Oil')
        if 'USD_THB' in merged_df.columns: features.append('USD_THB')
        if 'Rainfall' in merged_df.columns: features.append('Rainfall')
        
        logger.info(f"Using XGBoost with features: {features}")
        
        merged_df['day_of_week'] = merged_df.index.dayofweek
        merged_df['day_of_month'] = merged_df.index.day
        merged_df['target'] = merged_df['price'].shift(-1)
        
        train_df = merged_df.dropna(subset=['target'])
        
        X = train_df[features]
        y = train_df['target']
        
        model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        model.fit(X, y)
        
        forecast_dates = []
        forecast_prices = []
        
        current_features = merged_df.iloc[-1][features].copy()
        current_date = merged_df.index[-1]
        
        for i in range(1, days + 1):
            pred_date = current_date + pd.Timedelta(days=i)
            forecast_dates.append(pred_date)
            
            current_features['day_of_week'] = pred_date.dayofweek
            current_features['day_of_month'] = pred_date.day
            
            # Use exogenous data for prediction if available (or carry last known)
            for feat in ['Crude_Oil', 'USD_THB', 'Rainfall']:
                if feat in df_ext.columns:
                    if pred_date in df_ext.index:
                        current_features[feat] = df_ext.loc[pred_date, feat]
                    # else: current_features[feat] stays as last known
            
            X_pred = pd.DataFrame([current_features])
            pred_price = model.predict(X_pred)[0]
            forecast_prices.append(pred_price)
            current_features['price'] = pred_price
            
        forecast_df = pd.DataFrame({'predicted_price': forecast_prices}, index=forecast_dates)
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
