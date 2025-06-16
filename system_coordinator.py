import asyncio
import logging
import json
import os
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional

from agents.headline_classifier_agent import HeadlineClassifierAgent
from agents.sentiment_aggregator_agent import SentimentAggregatorAgent
from agents.signal_decision_agent import SignalDecisionAgent

# Try to import the new Alpha Vantage agent
try:
    from agents.alpha_vantage_sentiment_agent import AlphaVantageSentimentAgent
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError:
    ALPHA_VANTAGE_AVAILABLE = False
    logging.warning("Alpha Vantage sentiment agent not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SystemCoordinator")

class SystemCoordinator:
    """
    Coordinates the flow of data between agents and manages the system state.
    """
    
    def __init__(self, alpha_vantage_api_key: Optional[str] = None, use_alpha_vantage_sentiment: bool = False):
        # Create log directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Initialize sentiment analysis agent
        if use_alpha_vantage_sentiment and alpha_vantage_api_key and ALPHA_VANTAGE_AVAILABLE:
            logger.info("Using Alpha Vantage enhanced sentiment analysis")
            self.headline_classifier = AlphaVantageSentimentAgent(alpha_vantage_api_key)
        else:
            logger.info("Using NER-based sentiment analysis")
            self.headline_classifier = HeadlineClassifierAgent()
        
        # Initialize other agents
        self.sentiment_aggregator = SentimentAggregatorAgent(window_minutes=8*60)  # 8 hours window
        self.signal_decision = SignalDecisionAgent()  # Uses updated thresholds: 0.7/-0.7, min 2 headlines
        
        # Initialize state
        self.latest_signals = {}
        self.signal_history = []
        
        # Initialize event listeners
        self.signal_listeners = []
        
        # Configuration
        self.config = {
            "tickertick_enabled": True,  # We're using TickerTick for news
            "alpha_vantage_sentiment_enabled": use_alpha_vantage_sentiment and alpha_vantage_api_key and ALPHA_VANTAGE_AVAILABLE,
            "sentiment_aggregator_enabled": True,
            "api_key_provided": bool(alpha_vantage_api_key),
            "alpha_vantage_available": ALPHA_VANTAGE_AVAILABLE
        }
    
    def add_signal_listener(self, listener):
        """Add a listener for new signals."""
        self.signal_listeners.append(listener)
    
    async def _notify_signal_listeners(self, signals):
        """Notify all listeners of new signals."""
        for listener in self.signal_listeners:
            await listener(signals)
    
    def _sanitize_data(self, data: Any) -> Any:
        """
        Recursively convert numpy types to native Python types for JSON serialization.
        
        Args:
            data: Data that may contain numpy types
            
        Returns:
            Data with numpy types converted to native Python types
        """
        if isinstance(data, dict):
            return {key: self._sanitize_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self._sanitize_data(item) for item in data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif hasattr(data, 'item'):  # Handle numpy scalars
            return data.item()
        else:
            return data
    
    async def process_headline(self, headline: str) -> Dict[str, Any]:
        """
        Process a single headline through the entire pipeline.
        
        Args:
            headline: The financial headline to process
            
        Returns:
            The final trading signals generated from the headline
        """
        timestamp = datetime.now().isoformat()
        
        try:
            # Step 1: For headline-only processing (fallback), we need to skip ticker extraction
            # since this method is now primarily for legacy support
            tickers = []  # No ticker extraction for headline-only processing
            
            if not tickers:
                logger.info(f"No tickers available for headline-only processing: {headline}")
                return {}
            
            # Step 2: Classify headline sentiment (with empty tickers for legacy support)
            sentiment_data = await self.headline_classifier.process(headline, tickers=tickers)
            
            # Step 3: Aggregate sentiment for the extracted tickers
            aggregated_data = await self.sentiment_aggregator.process((timestamp, sentiment_data, tickers))
            
            # Step 4: Generate trading signals
            signals = await self.signal_decision.process(aggregated_data)
            
            # Update state
            self.latest_signals = signals
            
            # Create history entry
            history_entry = {
                "timestamp": timestamp,
                "headline": headline,
                "sentiment": sentiment_data,
                "tickers": tickers,
                "aggregated_sentiment": aggregated_data,
                "signals": signals
            }
            
            self.signal_history.append(history_entry)
            
            # Keep history manageable (last 100 entries)
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]
            
            # Notify listeners
            await self._notify_signal_listeners(signals)
            
            logger.info(f"Processed headline: {headline[:50]}... -> Generated {len(signals)} signals")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error processing headline '{headline}': {e}")
            return {}
    
    async def process_news_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a news article that already has ticker information (e.g., from TickerTick).
        This is more efficient as it skips ticker extraction.
        
        Args:
            article: News article with fields like 'headline', 'tickers', 'timestamp', etc.
            
        Returns:
            The final trading signals generated from the article
        """
        headline = article.get('headline', '')
        tickers = article.get('tickers', [])
        timestamp = article.get('timestamp', datetime.now().isoformat())
        
        try:
            if not headline:
                logger.warning("Article has no headline")
                return {}
            
            if not tickers:
                logger.info(f"No tickers found for article: {headline}")
                return {}
            
            # Step 1: Classify headline sentiment (with pre-provided tickers)
            sentiment_data = await self.headline_classifier.process(headline, tickers=tickers)
            
            # Step 2: Skip ticker extraction since we already have tickers
            # Convert TickerTick format (e.g., "AAPL") to our internal format if needed
            processed_tickers = []
            for ticker in tickers:
                # Remove 'tt:' prefix if present and convert to uppercase
                clean_ticker = ticker.replace('tt:', '').upper()
                processed_tickers.append(clean_ticker)
            
            # Step 3: Aggregate sentiment for the provided tickers
            aggregated_data = await self.sentiment_aggregator.process((timestamp, sentiment_data, processed_tickers))
            
            # Step 4: Generate trading signals
            signals = await self.signal_decision.process(aggregated_data)
            
            # Update state
            self.latest_signals = signals
            
            # Create history entry
            history_entry = {
                "timestamp": timestamp,
                "headline": headline,
                "sentiment": sentiment_data,
                "tickers": processed_tickers,
                "aggregated_sentiment": aggregated_data,
                "signals": signals,
                "article_id": article.get('id'),
                "source": article.get('source', ''),
                "url": article.get('url', '')
            }
            
            self.signal_history.append(history_entry)
            
            # Keep history manageable (last 100 entries)
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]
            
            # Notify listeners
            await self._notify_signal_listeners(signals)
            
            logger.info(f"Processed article: {headline[:50]}... -> Generated {len(signals)} signals for {len(processed_tickers)} tickers")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error processing article '{headline}': {e}")
            return {}
    
    async def get_latest_signals(self) -> Dict[str, Any]:
        """Get the latest trading signals."""
        # Sanitize the data to convert numpy types to native Python types
        return self._sanitize_data(self.latest_signals)
    
    async def get_signals_by_ticker(self) -> Dict[str, Any]:
        """
        Get the current aggregated signals organized by ticker.
        
        Returns:
            Dictionary with tickers as keys and their signal/sentiment data as values
        """
        signals_by_ticker = {}
        
        # Get the latest signals and organize by ticker
        for ticker, signal_data in self.latest_signals.items():
            signals_by_ticker[ticker] = {
                "ticker": ticker,
                "signal": signal_data.get("signal", "FLAT"),
                "confidence": signal_data.get("confidence", 0.0),
                "sentiment_score": signal_data.get("sentiment", 0.0),  # Fixed key name
                "volatility": signal_data.get("volatility", 0.0),
                "trend": signal_data.get("trend", "flat"),
                "headline_count": signal_data.get("headline_count", 0),
                "latest_score": signal_data.get("latest_score", 0.0)
            }
        
        # Sanitize the data to convert numpy types to native Python types
        return self._sanitize_data(signals_by_ticker)
    
    async def get_signal_history(self) -> List[Dict[str, Any]]:
        """Get the history of trading signals."""
        # Sanitize the data to convert numpy types to native Python types
        return self._sanitize_data(self.signal_history)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status and configuration."""
        return {
            "status": "running",
            "configuration": self.config,
            "total_headlines_processed": len(self.signal_history),
            "latest_signals_count": len(self.latest_signals),
            "sentiment_agent": self.headline_classifier.__class__.__name__
        }