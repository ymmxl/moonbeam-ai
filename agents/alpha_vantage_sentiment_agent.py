import logging
import requests
import asyncio
from typing import Dict, Any, Optional
from .base_agent import BaseAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AlphaVantageSentimentAgent")

class AlphaVantageSentimentAgent(BaseAgent):
    """
    Enhanced sentiment analysis agent that combines Alpha Vantage's sentiment data
    with our own classification logic.
    """
    
    def __init__(self, api_key: str):
        super().__init__("AlphaVantageSentimentAgent")
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        
        # Keyword-based sentiment classification (fallback)
        self.positive_keywords = [
            "surge", "jump", "rise", "beat", "exceed", "growth", "profit", "gain",
            "strong", "record", "upgrade", "buy", "bullish", "optimistic", "positive",
            "expansion", "partnership", "acquisition", "breakthrough", "success"
        ]
        
        self.negative_keywords = [
            "plunge", "drop", "fall", "miss", "decline", "loss", "weak", "poor",
            "downgrade", "sell", "bearish", "pessimistic", "negative", "concern",
            "layoff", "scandal", "controversy", "warning", "threat", "risk"
        ]
    
    def _get_alpha_vantage_sentiment(self, headline: str) -> Optional[Dict[str, Any]]:
        """
        Get sentiment analysis from Alpha Vantage for a specific headline.
        
        Args:
            headline: The headline to analyze
            
        Returns:
            Sentiment data from Alpha Vantage or None if unavailable
        """
        try:
            # For real-time sentiment, we would need to search for articles
            # that match the headline. This is a simplified approach.
            params = {
                'function': 'NEWS_SENTIMENT',
                'apikey': self.api_key,
                'limit': 1,
                'sort': 'LATEST'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'feed' in data and data['feed']:
                # Get the most recent article's sentiment
                article = data['feed'][0]
                return {
                    'overall_sentiment_score': article.get('overall_sentiment_score', 0.0),
                    'overall_sentiment_label': article.get('overall_sentiment_label', 'Neutral'),
                    'ticker_sentiment': article.get('ticker_sentiment', [])
                }
            
        except Exception as e:
            logger.warning(f"Could not get Alpha Vantage sentiment: {e}")
        
        return None
    
    def _keyword_based_sentiment(self, headline: str) -> Dict[str, Any]:
        """
        Fallback keyword-based sentiment analysis.
        
        Args:
            headline: The headline to analyze
            
        Returns:
            Sentiment classification with confidence
        """
        headline_lower = headline.lower()
        
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in headline_lower)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in headline_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.6 + (positive_count * 0.1), 0.9)
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(0.6 + (negative_count * 0.1), 0.9)
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "positive_signals": positive_count,
            "negative_signals": negative_count,
            "method": "keyword_based"
        }
    
    def _convert_alpha_vantage_sentiment(self, av_sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Alpha Vantage sentiment format to our internal format.
        
        Args:
            av_sentiment: Alpha Vantage sentiment data
            
        Returns:
            Our standardized sentiment format
        """
        score = float(av_sentiment.get('overall_sentiment_score', 0.0))
        label = av_sentiment.get('overall_sentiment_label', 'Neutral').lower()
        
        # Convert Alpha Vantage's sentiment to our format
        if label == 'bullish' or score > 0.2:
            sentiment = "positive"
            confidence = min(0.7 + abs(score) * 0.3, 0.95)
        elif label == 'bearish' or score < -0.2:
            sentiment = "negative"
            confidence = min(0.7 + abs(score) * 0.3, 0.95)
        else:
            sentiment = "neutral"
            confidence = 0.6
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "alpha_vantage_score": score,
            "alpha_vantage_label": label,
            "method": "alpha_vantage"
        }
    
    def _combine_sentiment_analyses(self, av_sentiment: Dict[str, Any], keyword_sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine Alpha Vantage sentiment with keyword-based sentiment.
        
        Args:
            av_sentiment: Alpha Vantage sentiment analysis
            keyword_sentiment: Our keyword-based sentiment analysis
            
        Returns:
            Combined sentiment analysis
        """
        # Weight Alpha Vantage more heavily since it's more sophisticated
        av_weight = 0.7
        keyword_weight = 0.3
        
        # Convert sentiment to numeric scores for averaging
        sentiment_to_score = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        score_to_sentiment = {1.0: "positive", 0.0: "neutral", -1.0: "negative"}
        
        av_score = sentiment_to_score[av_sentiment["sentiment"]]
        keyword_score = sentiment_to_score[keyword_sentiment["sentiment"]]
        
        # Weighted average
        combined_score = (av_score * av_weight) + (keyword_score * keyword_weight)
        
        # Determine final sentiment
        if combined_score > 0.2:
            final_sentiment = "positive"
        elif combined_score < -0.2:
            final_sentiment = "negative"
        else:
            final_sentiment = "neutral"
        
        # Combine confidences
        combined_confidence = (av_sentiment["confidence"] * av_weight) + (keyword_sentiment["confidence"] * keyword_weight)
        
        return {
            "sentiment": final_sentiment,
            "confidence": round(combined_confidence, 3),
            "combined_score": round(combined_score, 3),
            "alpha_vantage_sentiment": av_sentiment,
            "keyword_sentiment": keyword_sentiment,
            "method": "combined"
        }
    
    async def process(self, headline: str) -> Dict[str, Any]:
        """
        Process a headline and return enhanced sentiment analysis.
        
        Args:
            headline: The headline to analyze
            
        Returns:
            Enhanced sentiment analysis result
        """
        try:
            # Get keyword-based sentiment (always available)
            keyword_sentiment = self._keyword_based_sentiment(headline)
            
            # Try to get Alpha Vantage sentiment
            av_sentiment_raw = self._get_alpha_vantage_sentiment(headline)
            
            if av_sentiment_raw:
                # Convert Alpha Vantage format
                av_sentiment = self._convert_alpha_vantage_sentiment(av_sentiment_raw)
                
                # Combine both analyses
                result = self._combine_sentiment_analyses(av_sentiment, keyword_sentiment)
            else:
                # Fall back to keyword-based only
                result = keyword_sentiment
            
            result["headline"] = headline
            return result
            
        except Exception as e:
            logger.error(f"Error processing headline '{headline}': {e}")
            # Return neutral sentiment as fallback
            return {
                "headline": headline,
                "sentiment": "neutral",
                "confidence": 0.5,
                "method": "error_fallback",
                "error": str(e)
            } 