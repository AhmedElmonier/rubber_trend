import feedparser
from textblob import TextBlob
import logging
import urllib.parse

logger = logging.getLogger(__name__)

def fetch_and_analyze_news(query="rubber price OR latex market"):
    """
    Fetches news from Google News RSS for the given query and calculates average sentiment.
    Returns: (Sentiment Label, Average Score, Top Headlines)
    """
    try:
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            logger.warning("No news found for sentiment analysis.")
            return "Neutral", 0.0, []
            
        total_score = 0
        article_count = 0
        top_headlines = []
        
        for entry in feed.entries[:10]: # Analyze top 10 articles
            title = entry.title
            
            # Use TextBlob for simple polarity scoring (-1 to 1)
            blob = TextBlob(title)
            score = blob.sentiment.polarity
            
            total_score += score
            article_count += 1
            
            # Keep top 3 for the report
            if len(top_headlines) < 3:
                top_headlines.append(f"- {title} (Score: {score:.2f})")
                
        avg_score = total_score / article_count if article_count > 0 else 0
        
        # Determine Label
        if avg_score > 0.1:
            label = "Bullish ⭐"
        elif avg_score < -0.1:
            label = "Bearish 🔻"
        else:
            label = "Neutral ➖"
            
        logger.info(f"Sentiment Analysis Complete: {label} ({avg_score:.2f})")
        return label, avg_score, top_headlines
        
    except Exception as e:
        logger.error(f"Error during sentiment analysis: {e}")
        return "Unknown", 0.0, []

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    label, score, headlines = fetch_and_analyze_news()
    print(f"Overall Sentiment: {label} (Score: {score:.2f})")
    print("Top Headlines:")
    for h in headlines:
        print(h)
