import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import logging
import warnings

# Ignore statsmodels warnings for better output
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

def generate_forecast(df: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """
    Generates a forecast for the next `days` using ARIMA.
    Expects df with a 'date' datetime index and a 'price' column.
    """
    if df.empty or len(df) < 10:
        logger.warning("Not enough data to forecast. Returning empty dataframe.")
        return pd.DataFrame()

    df = df.sort_index()

    try:
        model = ARIMA(df['price'], order=(1, 1, 1))
        fitted = model.fit()

        forecast = fitted.forecast(steps=days)
        
        last_date = df.index[-1]
        forecast_dates = [last_date + pd.Timedelta(days=i) for i in range(1, days + 1)]
        
        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'predicted_price': forecast.values
        })
        forecast_df.set_index('date', inplace=True)
        return forecast_df

    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        return pd.DataFrame()
