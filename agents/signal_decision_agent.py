from typing import Dict, Any, Literal
from .base_agent import BaseAgent

SignalType = Literal["LONG", "SHORT", "FLAT"]

class SignalDecisionAgent(BaseAgent):
    """
    Agent that generates trading signals based on aggregated sentiment scores.
    """
    
    def __init__(self, long_threshold: float = 0.7, short_threshold: float = -0.7, min_headline_count: int = 2):
        super().__init__("SignalDecision")
        self.long_threshold = long_threshold
        self.short_threshold = short_threshold
        self.min_headline_count = min_headline_count
    
    async def process(self, aggregated_data: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, Any]]:
        """
        Generate trading signals based on aggregated sentiment scores.
        
        Args:
            aggregated_data: Dictionary mapping tickers to their aggregated sentiment data
                Expected format for each ticker:
                {
                    "avg_sentiment": float,
                    "max_sentiment": float,
                    "min_sentiment": float,
                    "volatility": float,
                    "count": int,
                    "latest_score": float,
                    "trend": str  # "up", "down", or "flat"
                }
                
        Returns:
            Dictionary mapping tickers to their trading signals
        """
        signals = {}
        
        for ticker, data in aggregated_data.items():
            avg_sentiment = data["avg_sentiment"]
            count = data["count"]
            volatility = data["volatility"]
            trend = data["trend"]
            latest_score = data["latest_score"]
            
            # Apply decision rules based on average sentiment and minimum headline count
            # Only generate LONG/SHORT signals if we have enough headlines
            if count >= self.min_headline_count:
                if avg_sentiment > self.long_threshold:
                    signal = "LONG"
                elif avg_sentiment < self.short_threshold:
                    signal = "SHORT"
                else:
                    signal = "FLAT"
            else:
                # If we don't have enough headlines, always generate FLAT signal
                signal = "FLAT"
            
            # Calculate confidence based on multiple factors:
            # 1. Number of headlines (more data = higher confidence)
            # 2. Low volatility = higher confidence
            # 3. Trend consistency = higher confidence
            
            # Base confidence from count (0.1 to 1.0)
            count_confidence = min(0.1 + (count * 0.1), 1.0)
            
            # Volatility confidence (lower volatility = higher confidence)
            # Normalize volatility to 0-1 range and invert
            volatility_confidence = max(0.1, 1.0 - min(volatility / 2.0, 1.0))
            
            # Trend confidence (consistent trend = higher confidence)
            trend_confidence = 0.8 if trend in ["up", "down"] else 0.5
            
            # Combine confidence factors (weighted average)
            signal_confidence = (
                count_confidence * 0.4 +
                volatility_confidence * 0.4 +
                trend_confidence * 0.2
            )
            
            # Ensure confidence is between 0 and 1
            signal_confidence = max(0.0, min(1.0, signal_confidence))
            
            signals[ticker] = {
                "signal": signal,
                "confidence": signal_confidence,
                "sentiment": avg_sentiment,
                "headline_count": count,
                "volatility": volatility,
                "trend": trend,
                "latest_score": latest_score
            }
        
        return signals