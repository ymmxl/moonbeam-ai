import re
from typing import Dict, List, Literal, Union, Optional
try:
    from .base_agent import BaseAgent
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.base_agent import BaseAgent
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification
import torch
import torch.nn.functional as F
import numpy as np

class HeadlineClassifierAgent(BaseAgent):
    """Agent that classifies financial headlines as positive, neutral, or negative and extracts tickers."""
    
    def __init__(self):
        super().__init__("HeadlineClassifier")
        
        # Load sentiment analysis model
        self.sentiment_model_name = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
        self.label_map = {0: "negative", 1: "neutral", 2: "positive"}
        self.sentiment_classifier = AutoModelForSequenceClassification.from_pretrained(self.sentiment_model_name)
        self.sentiment_tokenizer = AutoTokenizer.from_pretrained(self.sentiment_model_name)
        
        # Load NER model for ticker extraction
        try:
            self.ner_model_name = "Jean-Baptiste/roberta-ticker"
            self.ner_tokenizer = AutoTokenizer.from_pretrained(self.ner_model_name)
            self.ner_model = AutoModelForTokenClassification.from_pretrained(self.ner_model_name)
            self.ner_pipeline = pipeline("ner", 
                                       model=self.ner_model,
                                       tokenizer=self.ner_tokenizer,
                                       aggregation_strategy="simple")
            self.ner_available = True
            self.logger.info("NER model loaded successfully for ticker extraction")
        except Exception as e:
            self.logger.warning(f"Failed to load NER model: {e}. Using regex fallback only.")
            self.ner_available = False
            self.ner_pipeline = None
    
    def _extract_tickers_from_entities(self, entities: List[Dict]) -> List[str]:
        """
        Extract potential tickers from NER entities.
        
        Args:
            entities: List of entities from NER model
            
        Returns:
            List of potential ticker symbols
        """
        tickers = []
        ticker_patterns = [
            r'\b[A-Z]{1,5}\b',  # 1-5 uppercase letters
            r'\$[A-Z]{1,5}\b',  # Dollar sign followed by 1-5 uppercase letters
        ]
        
        for entity in entities:
            entity_text = entity.get('word', '').strip()
            entity_label = entity.get('entity_group', '').upper()
            
            # Look for organizations or miscellaneous entities that could be tickers
            if entity_label in ['ORG', 'MISC', 'PER']:
                # Check if entity matches ticker patterns
                for pattern in ticker_patterns:
                    if re.match(pattern, entity_text):
                        # Additional validation: typical ticker characteristics
                        clean_ticker = entity_text.replace('$', '').upper()
                        if (2 <= len(clean_ticker) <= 5 and 
                            clean_ticker.isalpha() and 
                            clean_ticker not in ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BY', 'NEWS', 'STOCK', 'MARKET', 'TODAY', 'TRUMP', 'WITH', 'FROM', 'WILL', 'SAID', 'THIS', 'THAT', 'THEY', 'WERE', 'BEEN', 'HAVE', 'DOES', 'WHEN', 'WHERE', 'WHAT', 'WHO', 'HOW', 'WHY', 'WHICH']):
                            tickers.append(clean_ticker)
        
        return list(set(tickers))  # Remove duplicates
    
    def _extract_tickers_regex_fallback(self, text: str) -> List[str]:
        """
        Extract ticker symbols using regex patterns as fallback.
        
        Args:
            text: Input text to extract tickers from
            
        Returns:
            List of ticker symbols, empty list if none found
        """
        tickers = []
        
        # Pattern for potential ticker symbols
        ticker_patterns = [
            r'\$([A-Z]{1,5})\b',  # $AAPL format
            r'\b([A-Z]{2,5})\b',  # AAPL format (2-5 uppercase letters)
        ]
        
        for pattern in ticker_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Filter out common false positives
                if match not in ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BY', 'NEWS', 'STOCK', 'MARKET', 'TODAY', 'TRUMP', 'WITH', 'FROM', 'WILL', 'SAID', 'THIS', 'THAT', 'THEY', 'WERE', 'BEEN', 'HAVE', 'DOES', 'WHEN', 'WHERE', 'WHAT', 'WHO', 'HOW', 'WHY', 'WHICH', 'SEC', 'CEO', 'CFO', 'IPO', 'FDA', 'API', 'USA']:
                    tickers.append(match.upper())
        
        return list(set(tickers))  # Remove duplicates
    
    def _round_sentiment_score(self, score: float) -> float:
        """
        Round sentiment score to 5 decimal places and handle very small numbers.
        
        Args:
            score: Raw sentiment score from the model
            
        Returns:
            Rounded sentiment score
        """
        # Round to 5 decimal places
        rounded_score = round(score, 5)
        
        # If the absolute value is very small (< 0.0001), treat as 0
        # This prevents scientific notation like -4e-05
        if abs(rounded_score) < 0.0001:
            return 0.0
        
        return rounded_score
    
    def extract_tickers(self, text: str) -> List[str]:
        """
        Extract ticker symbols from text using NER model or regex fallback.
        
        Args:
            text: Input text to extract tickers from
            
        Returns:
            List of ticker symbols, empty list if none found
        """
        tickers = []
        
        try:
            if self.ner_available and self.ner_pipeline:
                # Use NER model for entity extraction
                # entities = self.ner_pipeline(text)
                # tickers = self._extract_tickers_from_entities(entities)
                tickers = self.ner_pipeline(text)
                
                if tickers:
                    self.logger.info(f"NER extracted tickers: {tickers}")
                else:
                    # Fallback to regex if NER doesn't find anything
                    tickers = self._extract_tickers_regex_fallback(text)
                    if tickers:
                        self.logger.info(f"Regex fallback extracted tickers: {tickers}")
            else:
                # Use regex fallback if NER is not available
                tickers = self._extract_tickers_regex_fallback(text)
                if tickers:
                    self.logger.info(f"Regex extracted tickers: {tickers}")
        
        except Exception as e:
            self.logger.warning(f"Error in ticker extraction: {e}. Skipping ticker extraction.")
            tickers = []
        
        return tickers
    
    async def process(self, headline: str, tickers: Optional[List[str]] = None) -> Dict[str, Union[str, float, List[str]]]:
        """
        Classify the sentiment of a financial headline.
        
        Args:
            headline: The financial headline to classify
            tickers: Optional list of ticker symbols (from TickerTick API)
            
        Returns:
            A dictionary with sentiment classification, confidence score, and tickers
        """
        # Sentiment analysis
        inputs = self.sentiment_tokenizer(headline, return_tensors="pt", truncation=True)
        with torch.no_grad():
            outputs = self.sentiment_classifier(**inputs)
            probs = F.softmax(outputs.logits, dim=-1).detach().cpu()
            positive_prob = probs[0][2].item()
            negative_prob = probs[0][0].item()
            neutral_prob = probs[0][1].item()
            raw_sentiment_score = (positive_prob*2) + (negative_prob*-2) + (neutral_prob*0)
            sentiment_score = self._round_sentiment_score(raw_sentiment_score)
            sentiment_label = self.label_map[torch.argmax(probs).item()]
        
        # Use provided tickers or fallback to extraction if none provided
        if tickers is not None:
            final_tickers = tickers
        else:
            # Fallback: extract tickers if none provided (for backward compatibility)
            final_tickers = self._extract_tickers_regex_fallback(headline)
        
        result = {
            "label": sentiment_label,
            "sentiment_score": sentiment_score,
            "tickers": final_tickers,
            "ticker_count": len(final_tickers)
        }
        
        return result

if __name__ == "__main__":
    import asyncio
    
    async def test_classifier():
        c = HeadlineClassifierAgent()
        
        # Test headlines with known tickers
        test_headlines = [
            "SEC fines coinbase $100 million for fraud",
            "Apple (AAPL) reports record quarterly earnings",
            "Tesla stock surges 15% after strong delivery numbers",
            "$MSFT announces new AI partnership",
            "NVIDIA Corp beats earnings expectations",
            "Amazon stock drops on weak guidance"
        ]
        
        for headline in test_headlines:
            result = await c.process(headline)
            print(f"Headline: {headline}")
            print(f"Result: {result}")
            print("-" * 50)
    
    asyncio.run(test_classifier())

# sentiment score = (P_positive*1) + (P_negative*-1) + (P_neutral*0)
#time decay= sentiment score * e^(-time_decay_rate * time_since_publication)