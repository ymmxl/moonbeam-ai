import re
from typing import Dict, List, Literal, Union
from .base_agent import BaseAgent

SentimentType = Literal["positive", "neutral", "negative"]

class HeadlineClassifierAgent(BaseAgent):
    """Agent that classifies financial headlines as positive, neutral, or negative."""
    
    def __init__(self):
        super().__init__("HeadlineClassifier")
        # Simple keyword-based classifier
        # In a real implementation, this would be a fine-tuned model
        self.positive_keywords = [
            "record", "beat", "surge", "jump", "rise", "gain", "profit", 
            "growth", "positive", "up", "higher", "strong", "exceed", 
            "outperform", "success", "bullish", "rally", "soar"
        ]
        
        self.negative_keywords = [
            "miss", "drop", "fall", "decline", "loss", "down", "lower",
            "weak", "struggle", "underperform", "fail", "bearish", "plunge",
            "crash", "tumble", "disappoint", "cut", "layoff", "bankruptcy"
        ]
    
    async def process(self, headline: str) -> Dict[str, Union[str, float]]:
        """
        Classify the sentiment of a financial headline.
        
        Args:
            headline: The financial headline to classify
            
        Returns:
            A dictionary with the sentiment classification and confidence score
        """
        headline_lower = headline.lower()
        
        # Count positive and negative keywords
        positive_count = sum(1 for word in self.positive_keywords if word in headline_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in headline_lower)
        
        # Determine sentiment based on keyword counts
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.5 + (positive_count - negative_count) * 0.1, 0.9)
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(0.5 + (negative_count - positive_count) * 0.1, 0.9)
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": confidence
        }