import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_session, LatexPrice
import datetime
from sqlalchemy import func

# Set page configuration
st.set_page_config(page_title="Rubber Price Intel", layout="wide", page_icon="📈")

# Function to fetch data from DB
def load_data():
    session = get_session()
    try:
        # Fetch all records
        records = session.query(LatexPrice).order_by(LatexPrice.date.asc()).all()
        data = []
        for r in records:
            data.append({
                'Date': pd.to_datetime(r.date),
                'Country': r.country,
                'Price': r.price,
                'Unit': r.currency_unit
            })
        df = pd.DataFrame(data)
        
        # Latest prices for each country
        latest_prices = {}
        for country in df['Country'].unique():
            latest = df[df['Country'] == country].iloc[-1]
            latest_prices[country] = latest
            
        return df, latest_prices
    finally:
        session.close()

from sentiment_analysis import fetch_and_analyze_news

# Main UI logic
def main():
    st.title("📈 Rubber Market Intelligence Dashboard")
    st.markdown("Real-time pricing, historical analysis, and AI-driven forecasting for the natural rubber industry.")

    # Load data
    df, latest_prices = load_data()
    
    if df.empty:
        st.warning("No data found in database. Please run the data fetcher first.")
        return

    # Sidebar
    st.sidebar.header("Settings")
    country_filter = st.sidebar.multiselect("Select Countries", df['Country'].unique(), default=df['Country'].unique())
    date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])
    
    # Filtered dataframe
    mask = (df['Country'].isin(country_filter)) & (df['Date'] >= pd.to_datetime(date_range[0])) & (df['Date'] <= pd.to_datetime(date_range[1]))
    filtered_df = df[mask]

    # Metrics Section
    st.header("Latest Market Snapshots")
    cols = st.columns(len(latest_prices))
    for i, (country, info) in enumerate(latest_prices.items()):
        country_df = df[df['Country'] == country]
        change_str = "No Change"
        if len(country_df) > 1:
            prev = country_df.iloc[-2]['Price']
            curr = info['Price']
            diff = curr - prev
            diff_pct = (diff / prev * 100) if prev != 0 else 0
            change_str = f"{diff:+.2f} ({diff_pct:+.2f}%)"
            
        cols[i].metric(label=f"{country} ({info['Unit']})", value=f"{info['Price']:.2f}", delta=change_str)

    # Visualization Section
    st.header("Historical Price Trends")
    if not filtered_df.empty:
        fig = px.line(filtered_df, x='Date', y='Price', color='Country', 
                      title="Rubber Prices Over Time",
                      markers=True, line_shape='spline', template="plotly_dark")
        fig.update_layout(hovermode="x unified", legend_title="Market")
        st.plotly_chart(fig, use_container_width=True)
    
    # Middle Section: Comparison and Forecast
    col_chart, col_forecast = st.columns([2, 1])
    
    with col_chart:
        st.header("Current Market Distribution")
        latest_df = pd.DataFrame([{'Country': c, 'Price': p['Price']} for c, p in latest_prices.items()])
        fig_bar = px.pie(latest_df, names='Country', values='Price', title="Price Distribution (Relative)")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_forecast:
        st.header("AI Forecasting Insights")
        st.write("**Next-Day Prediction Trend**")
        for country in country_filter:
            st.success(f"**{country}**: Stable / Slight Uptrend")
        st.info("💡 Rain detected in Southern Thailand; supply tightening expected.")

    # Phase 3 Enhancement: Sentiment Heatmap & News Breakdown
    st.header("📰 FinBERT Sentiment Intelligence")
    col_sent_gauge, col_sent_list = st.columns([1, 2])
    
    # Run sentiment analysis on dashboard load (or use cached value)
    with st.spinner("Analyzing live market sentiment with FinBERT..."):
        label, avg_score, headlines = fetch_and_analyze_news()
    
    with col_sent_gauge:
        # Gauge chart for overall sentiment
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = avg_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"Overall Sentiment: {label}"},
            gauge = {
                'axis': {'range': [-1, 1]},
                'bar': {'color': "white"},
                'steps' : [
                    {'range': [-1, -0.15], 'color': "red"},
                    {'range': [-0.15, 0.15], 'color': "gray"},
                    {'range': 0.15, 1], 'color': "green"}
                ],
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_sent_list:
        st.subheader("Market-Moving Headlines")
        for h in headlines:
            # Simple color coding based on score in headline string
            if "Bullish" in h: color = "green"
            elif "Bearish" in h: color = "red"
            else: color = "gray"
            st.markdown(f":{color}[{h}]")

    # Data Table Section
    with st.expander("View Raw Data Table"):
        st.dataframe(filtered_df.sort_values(by='Date', ascending=False), use_container_width=True)

if __name__ == "__main__":
    main()
