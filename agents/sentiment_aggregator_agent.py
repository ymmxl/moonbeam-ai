import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Any, Union
import pandas as pd
from .base_agent import BaseAgent

class SentimentAggregatorAgent(BaseAgent):
    """
    Agent that aggregates sentiment scores for tickers over a sliding time window.
    This agent focuses solely on sentiment aggregation and does NOT extract tickers.
    """
    
    def __init__(self, window_minutes: int = 5):
        super().__init__("SentimentAggregator")
        self.window_minutes = window_minutes
        self.sentiment_store = {}  # ticker -> deque of (datetime, sentiment_score)
    
    def _parse_timestamp(self, timestamp: Union[str, datetime, None]) -> datetime:
        """
        Convert timestamp string to datetime object with timezone awareness.
        
        Args:
            timestamp: Either a string timestamp, datetime object, or None
            
        Returns:
            datetime object with timezone information
        """
        # Handle None case
        if timestamp is None:
            self.logger.warning("Received None timestamp, using current time")
            return datetime.now(timezone.utc)
        
        if isinstance(timestamp, datetime):
            # If already a datetime, ensure it has timezone info
            if timestamp.tzinfo is None:
                return timestamp.replace(tzinfo=timezone.utc)
            return timestamp
        
        # Handle string timestamps
        if isinstance(timestamp, str):
            try:
                # Try parsing ISO format with timezone
                if timestamp.endswith('Z'):
                    # Replace 'Z' with '+00:00' for proper parsing
                    timestamp = timestamp[:-1] + '+00:00'
                
                dt = datetime.fromisoformat(timestamp)
                
                # Ensure timezone awareness
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                
                return dt
            except ValueError as e:
                self.logger.error(f"Failed to parse timestamp '{timestamp}': {e}")
                # Fallback to current time with UTC timezone
                return datetime.now(timezone.utc)
        
        # Fallback case for unexpected types
        self.logger.warning(f"Unexpected timestamp type: {type(timestamp)}, using current time")
        return datetime.now(timezone.utc)
    
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
            
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.window_minutes)
        
        # Keep only entries newer than the cutoff time
        # Now comparing datetime objects directly
        self.sentiment_store[ticker] = deque(
            [(ts, score) for ts, score in self.sentiment_store[ticker]
             if ts > cutoff_time],
            maxlen=100  # Limit the maximum size of the deque
        )
    
    async def process(self, data: Tuple[Union[str, datetime, None], Dict[str, Any], List[str]]) -> Dict[str, Dict[str, float]]:
        """
        Aggregate sentiment scores for tickers over the sliding window.
        
        Args:
            data: Tuple of (timestamp, sentiment_data, tickers)
                timestamp: ISO format timestamp string or datetime object
                sentiment_data: Dict with either:
                    - 'sentiment' and 'confidence' keys
                    - 'sentiment_score' and 'label' keys (from headline_classifier_agent)
                tickers: List of ticker symbols (from TickerTick API or manually provided)
                
        Returns:
            Dictionary mapping tickers to their aggregated sentiment data
        """
        timestamp_input, sentiment_data, tickers = data
        
        # Convert timestamp to datetime object
        timestamp = self._parse_timestamp(timestamp_input)
        
        # Validate input
        if not tickers:
            self.logger.warning("No tickers provided for sentiment aggregation")
            return {}
        
        # Extract sentiment score from different possible formats
        if "sentiment_score" in sentiment_data and "label" in sentiment_data:
            # Format from headline_classifier_agent.py
            score = sentiment_data["sentiment_score"]
        elif "sentiment_score" in sentiment_data:
            # Direct sentiment score
            score = sentiment_data["sentiment_score"]
        elif "sentiment" in sentiment_data and "confidence" in sentiment_data:
            # Legacy format with sentiment and confidence
            sentiment = sentiment_data["sentiment"]
            confidence = sentiment_data["confidence"]
            score = self._convert_sentiment_to_score(sentiment) * confidence
        else:
            self.logger.error(f"Invalid sentiment data format: {sentiment_data}")
            return {}
        
        # Store the sentiment data for each ticker
        for ticker in tickers:
            if ticker not in self.sentiment_store:
                self.sentiment_store[ticker] = deque(maxlen=100)
            
            # Now storing datetime object instead of string
            self.sentiment_store[ticker].append((timestamp, score))
            self._clean_old_data(ticker)
        
        # Calculate aggregated sentiment for each ticker
        result = {}
        for ticker, data_points in self.sentiment_store.items():
            if not data_points:
                continue
                
            # Calculate statistics
            scores = [score for _, score in data_points]
            count = len(scores)
            
            if count > 0:
                avg_sentiment = sum(scores) / count
                max_sentiment = max(scores)
                min_sentiment = min(scores)
                
                # Calculate volatility (standard deviation)
                variance = sum((score - avg_sentiment) ** 2 for score in scores) / count
                volatility = variance ** 0.5
                
                result[ticker] = {
                    "avg_sentiment": avg_sentiment,
                    "max_sentiment": max_sentiment,
                    "min_sentiment": min_sentiment,
                    "volatility": volatility,
                    "count": count,
                    "latest_score": scores[-1],  # Most recent sentiment score
                    "trend": "up" if len(scores) >= 2 and scores[-1] > scores[-2] else 
                            "down" if len(scores) >= 2 and scores[-1] < scores[-2] else "flat"
                }
        
        return result
    
    def get_ticker_history(self, ticker: str, minutes: int = None) -> List[Tuple[str, float]]:
        """
        Get sentiment history for a specific ticker.
        
        Args:
            ticker: The ticker symbol
            minutes: How many minutes back to look (default: use window_minutes)
            
        Returns:
            List of (timestamp, sentiment_score) tuples with ISO format timestamps
        """
        if ticker not in self.sentiment_store:
            return []
        
        if minutes is None:
            minutes = self.window_minutes
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        # Convert datetime objects back to ISO format strings for output
        return [
            (ts.isoformat(), score) for ts, score in self.sentiment_store[ticker]
            if ts > cutoff_time
        ]
    
    def get_all_tickers(self) -> List[str]:
        """Get all tickers currently being tracked."""
        return list(self.sentiment_store.keys())
    
    def clear_ticker_data(self, ticker: str) -> None:
        """Clear all sentiment data for a specific ticker."""
        if ticker in self.sentiment_store:
            self.sentiment_store[ticker].clear()
            self.logger.info(f"Cleared sentiment data for ticker: {ticker}")

if __name__ == "__main__":
    from base_agent import BaseAgent
    import asyncio
    
    async def test_sentiment_aggregator():
        aggregator = SentimentAggregatorAgent(window_minutes=10)  # Increased window for testing
        
        # Get current time for realistic test data
        now = datetime.now(timezone.utc)
        
        # Test data with different sentiment formats and timestamp types
        test_cases = [
            # Format 1: sentiment_score + label (from headline_classifier_agent) - recent timestamp
            ((now - timedelta(minutes=1)).isoformat(), {"sentiment_score": 1.5, "label": "positive"}, ["AAPL"]),
            
            # Format 2: sentiment + confidence (legacy) - recent timestamp  
            ((now - timedelta(minutes=2)).isoformat(), {"sentiment": "negative", "confidence": 0.8}, ["AAPL", "MSFT"]),
            
            # Format 3: direct sentiment_score with Z format
            ((now - timedelta(minutes=3)).isoformat().replace('+00:00', 'Z'), {"sentiment_score": 0.5}, ["MSFT"]),
            
            # Format 4: datetime object instead of string
            (now - timedelta(minutes=4), {"sentiment_score": 2.0, "label": "positive"}, ["AAPL"]),
            
            # Format 5: Test with basic ISO format (no timezone)
            ((now - timedelta(minutes=5)).replace(tzinfo=None).isoformat(), {"sentiment_score": -1.2, "label": "negative"}, ["TSLA"]),
        ]
        
        print("Testing Sentiment Aggregator with improved timestamp handling:")
        for i, test_case in enumerate(test_cases):
            print(f"\n--- Test Case {i+1} ---")
            result = await aggregator.process(test_case)
            print(f"Input timestamp: {test_case[0]} (type: {type(test_case[0])})")
            print(f"Input sentiment: {test_case[1]}")
            print(f"Input tickers: {test_case[2]}")
            print(f"Result: {result}")
        
        print(f"\nAll tracked tickers: {aggregator.get_all_tickers()}")
        print(f"AAPL history: {aggregator.get_ticker_history('AAPL')}")
        
        # Test with some edge cases
        print(f"\n--- Testing Edge Cases ---")
        
        # Test with malformed timestamp
        edge_case_1 = ("invalid-timestamp", {"sentiment_score": 1.0}, ["TEST"])
        result = await aggregator.process(edge_case_1)
        print(f"Malformed timestamp test result: {result}")
        
        # Test with None timestamp (should be handled gracefully)
        try:
            edge_case_2 = (None, {"sentiment_score": 1.0}, ["TEST2"])
            result = await aggregator.process(edge_case_2)
            print(f"None timestamp test result: {result}")
        except Exception as e:
            print(f"None timestamp test error (expected): {e}")
    
    asyncio.run(test_sentiment_aggregator())