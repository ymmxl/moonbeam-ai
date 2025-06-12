import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from agents.headline_classifier_agent import HeadlineClassifierAgent
from agents.ticker_mapper_agent import TickerMapperAgent
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
            logger.info("Using standard keyword-based sentiment analysis")
            self.headline_classifier = HeadlineClassifierAgent()
        
        # Initialize other agents
        self.ticker_mapper = TickerMapperAgent()
        self.sentiment_aggregator = SentimentAggregatorAgent(window_minutes=5)
        self.signal_decision = SignalDecisionAgent()
        
        # Initialize state
        self.latest_signals = {}
        self.signal_history = []
        
        # Initialize event listeners
        self.signal_listeners = []
        
        # Configuration
        self.config = {
            "gnews_enabled": True,  # We're using GNews for news
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
            # Step 1: Classify headline sentiment
            sentiment_data = await self.headline_classifier.run(headline)
            
            # Step 2: Extract ticker symbols from headline
            tickers = await self.ticker_mapper.run(headline)
            
            if not tickers:
                logger.info(f"No tickers found for headline: {headline}")
                return {}
            
            # Step 3: Aggregate sentiment for the extracted tickers
            aggregated_data = await self.sentiment_aggregator.run((timestamp, sentiment_data, tickers))
            
            # Step 4: Generate trading signals
            signals = await self.signal_decision.run(aggregated_data)
            
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
    
    async def get_latest_signals(self) -> Dict[str, Any]:
        """Get the latest trading signals."""
        return self.latest_signals
    
    async def get_signal_history(self) -> List[Dict[str, Any]]:
        """Get the history of trading signals."""
        return self.signal_history
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status and configuration."""
        return {
            "status": "running",
            "configuration": self.config,
            "total_headlines_processed": len(self.signal_history),
            "latest_signals_count": len(self.latest_signals),
            "sentiment_agent": self.headline_classifier.__class__.__name__
        }