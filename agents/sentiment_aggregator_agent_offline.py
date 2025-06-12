import time
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import pandas as pd
from .base_agent import BaseAgent

class SentimentAggregatorAgent(BaseAgent):
    """
    Agent that aggregates sentiment scores for tickers over a sliding time window.
    """
    
    def __init__(self, window_minutes: int = 5):
        super().__init__("SentimentAggregator")
        self.window_minutes = window_minutes
        self.sentiment_store = {}  # ticker -> deque of (timestamp, sentiment, confidence)
    
    def _convert_sentiment_to_score(self, sentiment: str) -> float:
        """Convert sentiment string to numerical score."""
        if sentiment == "positive":
            return 1.0
        elif sentiment == "negative":
            return -1.0
        else:  # neutral
            return 0.0
    
    def _clean_old_data(self, ticker: str) -> None:
        """Remove data older than the window from the store."""
        if ticker not in self.sentiment_store:
            return
            
        cutoff_time = datetime.now() - timedelta(minutes=self.window_minutes)
        
        # Keep only entries newer than the cutoff time
        self.sentiment_store[ticker] = deque(
            [(ts, sent, conf) for ts, sent, conf in self.sentiment_store[ticker]
             if datetime.fromisoformat(ts) > cutoff_time],
            maxlen=100  # Limit the maximum size of the deque
        )
    
    async def process(self, data: Tuple[str, Dict[str, Any], List[str]]) -> Dict[str, Dict[str, float]]:
        """
        Aggregate sentiment scores for tickers over the sliding window.
        
        Args:
            data: Tuple of (timestamp, sentiment_data, tickers)
                timestamp: ISO format timestamp
                sentiment_data: Dict with 'sentiment' and 'confidence' keys
                tickers: List of ticker symbols
                
        Returns:
            Dictionary mapping tickers to their aggregated sentiment data
        """
        timestamp, sentiment_data, tickers = data
        sentiment = sentiment_data["sentiment"]
        confidence = sentiment_data["confidence"]
        
        # Convert sentiment to score
        score = self._convert_sentiment_to_score(sentiment) * confidence
        
        # Store the sentiment data for each ticker
        for ticker in tickers:
            if ticker not in self.sentiment_store:
                self.sentiment_store[ticker] = deque(maxlen=100)
            
            self.sentiment_store[ticker].append((timestamp, score, confidence))
            self._clean_old_data(ticker)
        
        # Calculate aggregated sentiment for each ticker
        result = {}
        for ticker, data_points in self.sentiment_store.items():
            if not data_points:
                continue
                
            # Calculate weighted average sentiment
            total_score = sum(score for _, score, _ in data_points)
            total_confidence = sum(conf for _, _, conf in data_points)
            count = len(data_points)
            
            if count > 0:
                avg_sentiment = total_score / count
                avg_confidence = total_confidence / count
                
                result[ticker] = {
                    "avg_sentiment": avg_sentiment,
                    "count": count,
                    "confidence": avg_confidence
                }
        
        return result