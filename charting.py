import matplotlib.pyplot as plt
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

def generate_chart(country: str, history_df: pd.DataFrame, forecast_df: pd.DataFrame, output_dir: str = "charts"):
    """
    Generates a line chart with history and forecast for a specific country.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    plt.figure(figsize=(10, 6))
    
    if not list(history_df.index):
        if not forecast_df.empty:
            plt.plot(forecast_df.index, forecast_df['predicted_price'], label='Forecast (7 Days)', color='orange', linestyle='--', marker='x', markersize=4)
    else:
        unit = history_df['currency_unit'].iloc[0] if 'currency_unit' in history_df.columns else ''
        plt.plot(history_df.index, history_df['price'], label='Historical Price', color='blue', marker='o', markersize=4)

        if not forecast_df.empty:
            last_hist = history_df.iloc[[-1]]
            tmp_forecast = pd.DataFrame({'predicted_price': [last_hist['price'].values[0]]}, index=last_hist.index)
            tmp_forecast = pd.concat([tmp_forecast, forecast_df])
            plt.plot(tmp_forecast.index, tmp_forecast['predicted_price'], label='Forecast (7 Days)', color='orange', linestyle='--', marker='x', markersize=4)

    plt.title(f"{country} Latex Price & Forecast")
    plt.xlabel("Date")
    plt.ylabel(f"Price ({unit})" if not list(history_df.index) == [] else "Price")
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"{country}_price_chart.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath)
    plt.close()
    
    logger.info(f"Chart saved to {filepath}")
    return filepath
