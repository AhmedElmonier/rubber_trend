import feedparser
from textblob import TextBlob
import logging
import urllib.parse
import re

logger = logging.getLogger(__name__)

# Lazy initialization for FinBERT to save memory until used
_finbert_pipeline = None

def get_finbert_pipeline():
    global _finbert_pipeline
    if _finbert_pipeline is None:
        try:
            from transformers import pipeline
            logger.info("Initializing FinBERT pipeline (this may take a moment for the first time)...")
            # Using ProsusAI/finbert - one of the most popular financial sentiment models
            _finbert_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        except Exception as e:
            logger.error(f"Failed to load FinBERT: {e}. Falling back to TextBlob.")
            _finbert_pipeline = "FALLBACK"
    return _finbert_pipeline

def analyze_sentiment(text):
    """
    Analyzes sentiment using FinBERT, falling back to TextBlob if needed.
    Returns: (label, score) - score is normalized where 1.0 is most positive, -1.0 is most negative
    """
    pipe = get_finbert_pipeline()
    
    if pipe != "FALLBACK":
        try:
            # FinBERT returns labels: 'positive', 'negative', 'neutral'
            result = pipe(text[:512])[0] # Limit to 512 tokens for BERT
            label = result['label']
            score = result['score'] # Confidence score (0 to 1)
            
            if label == 'positive':
                return "Bullish", score
            elif label == 'negative':
                return "Bearish", -score
            else:
                return "Neutral", 0.0
        except Exception as e:
            logger.warning(f"FinBERT inference error: {e}. Using TextBlob fallback.")
            
    # TextBlob Fallback
    blob = TextBlob(text)
    score = blob.sentiment.polarity # -1 to 1
    if score > 0.1:
        return "Bullish", score
    elif score < -0.1:
        return "Bearish", score
    else:
        return "Neutral", 0.0

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
        
        # Analyze top 10 articles
        for entry in feed.entries[:10]:
            title = entry.title
            
            label, score = analyze_sentiment(title)
            
            total_score += score
            article_count += 1
            
            # Keep top 3 for the report
            if len(top_headlines) < 3:
                top_headlines.append(f"- {title} ({label}: {score:.2f})")
                
        avg_score = total_score / article_count if article_count > 0 else 0
        
        # Determine Final Label based on average score
        if avg_score > 0.15:
            final_label = "Bullish ⭐"
        elif avg_score < -0.15:
            final_label = "Bearish 🔻"
        else:
            final_label = "Neutral ➖"
            
        logger.info(f"Sentiment Analysis Complete: {final_label} ({avg_score:.2f})")
        return final_label, avg_score, top_headlines
        
    except Exception as e:
        logger.error(f"Error during sentiment analysis: {e}")
        return "Unknown", 0.0, []

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    label, score, headlines = fetch_and_analyze_news()
    print(f"\nOverall Sentiment: {label} (Score: {score:.2f})")
    print("Top Headlines with FinBERT Analysis:")
    for h in headlines:
        print(h)
