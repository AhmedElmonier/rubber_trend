import matplotlib.pyplot as plt
import pandas as pd
import os
import logging
import matplotlib.dates as mdates

logger = logging.getLogger(__name__)

def generate_chart(country: str, history_df: pd.DataFrame, forecast_df: pd.DataFrame, output_dir: str = "charts"):
    """
    Generates a professional, modernized line chart with history and forecast.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Use a modern dark theme style
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Background color customization
    fig.patch.set_facecolor('#121212')
    ax.set_facecolor('#1e1e1e')
    
    unit = history_df['currency_unit'].iloc[0] if not history_df.empty and 'currency_unit' in history_df.columns else ''
    
    if not history_df.empty:
        # Plot Historical Price with shadow/glow effect
        ax.plot(history_df.index, history_df['price'], label='Historical Trend', 
                color='#00d1ff', linewidth=3, marker='o', markersize=5, markerfacecolor='white', alpha=0.9)
        
        # Fill area under history
        ax.fill_between(history_df.index, history_df['price'], color='#00d1ff', alpha=0.1)

        # Annotate Last Price
        last_date = history_df.index[-1]
        last_price = history_df['price'].iloc[-1]
        ax.annotate(f'{last_price:.2f}', xy=(last_date, last_price), xytext=(8, 0),
                    textcoords='offset points', color='white', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', fc='#00d1ff', ec='none', alpha=0.8))

    if not forecast_df.empty:
        # Join history and forecast for a continuous line
        last_hist_val = history_df['price'].iloc[-1] if not history_df.empty else forecast_df['predicted_price'].iloc[0]
        last_hist_date = history_df.index[-1] if not history_df.empty else forecast_df.index[0] - pd.Timedelta(days=1)
        
        # Combine for plotting the forecast line
        f_dates = [last_hist_date] + list(forecast_df.index)
        f_prices = [last_hist_val] + list(forecast_df['predicted_price'])
        
        ax.plot(f_dates, f_prices, label='7-Day AI Forecast', 
                color='#ffcc00', linewidth=3, linestyle='--', marker='x', markersize=6)
        
        # Forecast Confidence Area (Simulated visual for Intel feel)
        ax.fill_between(f_dates, [p*0.98 for p in f_prices], [p*1.02 for p in f_prices], 
                        color='#ffcc00', alpha=0.05, label='Confidence Interval')

    # Formatting
    ax.set_title(f"📊 {country.upper()} MARKET ANALYSIS & AI PREDICTION", 
                 fontsize=16, fontweight='bold', color='#ffffff', pad=20)
    ax.set_ylabel(f"Price ({unit})", fontsize=12, color='#cccccc')
    ax.legend(loc='upper left', frameon=True, facecolor='#333333', edgecolor='none')
    
    # Grid and Spines
    ax.grid(True, linestyle='--', alpha=0.2, color='#555555')
    for spine in ax.spines.values():
        spine.set_visible(False)
        
    # Date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.xticks(rotation=0)

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    
    # Add watermark/branding
    fig.text(0.99, 0.01, 'Rubber Intel AI Pipeline', fontsize=10, color='#555555', 
             ha='right', va='bottom', alpha=0.7)

    filename = f"{country}_price_chart.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=120, facecolor=fig.get_facecolor())
    plt.close()
    
    logger.info(f"Modernized chart saved to {filepath}")
    return filepath
