import pytest
from unittest.mock import patch, MagicMock
from data_fetcher import fetch_price_from_news

@patch('feedparser.parse')
def test_fetch_price_from_news_india_success(mock_parse):
    # Mocking Google News RSS response
    mock_entry = MagicMock()
    mock_entry.title = "Natural rubber price hit an all-time high of Rs. 244 in domestic market"
    mock_parse.return_value.entries = [mock_entry]
    
    price, unit = fetch_price_from_news("rubber price RSS4 Kottayam today", "India", "INR/kg")
    
    assert price == 244.0
    assert unit == "INR/kg"

@patch('feedparser.parse')
def test_fetch_price_from_news_skip_change(mock_parse):
    # Mocking a change report that should be skipped
    mock_entry = MagicMock()
    mock_entry.title = "Rubber prices in Kerala drop Rs 25 in 27 days"
    mock_parse.return_value.entries = [mock_entry]
    
    result = fetch_price_from_news("rubber price RSS4 Kottayam today", "India", "INR/kg")
    
    # Should return None because it skipped the drop headline
    assert result is None

@patch('feedparser.parse')
def test_fetch_price_from_news_malaysia(mock_parse):
    mock_entry = MagicMock()
    mock_entry.title = "SMR 20 Price hits 840.50 Sen today"
    mock_parse.return_value.entries = [mock_entry]
    
    price, unit = fetch_price_from_news("Malaysia rubber", "Malaysia", "MYR/kg")
    
    # 840.50 Sen -> 8.405 MYR
    assert price == 8.405
    assert unit == "MYR/kg"

@patch('feedparser.parse')
def test_fetch_price_from_news_china(mock_parse):
    mock_entry = MagicMock()
    mock_entry.title = "TSR 20 price at 13050 RMB in Shanghai"
    mock_parse.return_value.entries = [mock_entry]
    
    price, unit = fetch_price_from_news("China rubber", "China", "CNY/ton")
    
    assert price == 13050.0
    assert unit == "CNY/ton"
