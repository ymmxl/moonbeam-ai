import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional, Callable, Awaitable
from .base_agent import BaseAgent
import sys
import os

# Add the parent directory to the path to import the fetcher
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tickertick_news_fetcher import TickerTickNewsFetcher

class TickerTickNewsAgent(BaseAgent):
    """
    Agent that fetches news from TickerTick API and processes it for sentiment analysis.
    This agent bypasses ticker extraction since TickerTick API already provides tickers.
    """
    
    def __init__(self, fetch_interval_seconds: int = 600):
        super().__init__("TickerTickNews")
        self.fetcher = TickerTickNewsFetcher()
        self.fetch_interval_seconds = max(fetch_interval_seconds, 60)  # Respect rate limits
        
        # Callback for processing each news story
        self.story_processor: Optional[Callable[[str, List[str], str], Awaitable[None]]] = None
        
        # Track processed stories to avoid duplicates
        self.processed_story_ids = set()
        self.max_processed_ids = 1000  # Limit memory usage
        
    def set_story_processor(self, processor: Callable[[str, List[str], str], Awaitable[None]]):
        """
        Set the callback function to process each news story.
        
        Args:
            processor: Async function that takes (headline, tickers, timestamp) and processes it
        """
        self.story_processor = processor
    
    async def process(self, input_data: Any = None) -> Dict[str, Any]:
        """
        Fetch latest news stories from TickerTick API.
        
        Args:
            input_data: Not used for this agent (it's a source agent)
            
        Returns:
            Dictionary with fetched stories and metadata
        """
        stories = await self.fetcher.fetch_latest_news()
        
        # Filter out already processed stories
        new_stories = []
        for story in stories:
            story_id = story.get("id")
            if story_id and story_id not in self.processed_story_ids:
                new_stories.append(story)
                self.processed_story_ids.add(story_id)
        
        # Limit memory usage by removing old processed IDs
        if len(self.processed_story_ids) > self.max_processed_ids:
            # Remove oldest 20% of processed IDs
            ids_to_remove = len(self.processed_story_ids) - int(self.max_processed_ids * 0.8)
            old_ids = list(self.processed_story_ids)[:ids_to_remove]
            for old_id in old_ids:
                self.processed_story_ids.discard(old_id)
        
        self.logger.info(f"Fetched {len(stories)} stories, {len(new_stories)} are new")
        
        # Process each new story if processor is set
        if self.story_processor and new_stories:
            for story in new_stories:
                try:
                    await self.story_processor(
                        story["headline"],
                        story["tickers"],
                        story["timestamp"]
                    )
                except Exception as e:
                    self.logger.error(f"Error processing story {story.get('id', 'unknown')}: {e}")
        
        return {
            "total_stories_fetched": len(stories),
            "new_stories_processed": len(new_stories),
            "api_usage": self.fetcher.get_api_usage_info(),
            "stories": new_stories
        }
    
    async def start_news_stream(self, 
                               headline_classifier,
                               sentiment_aggregator,
                               signal_decision_agent=None):
        """
        Start the continuous news stream and process through sentiment pipeline.
        
        Args:
            headline_classifier: Agent to classify headline sentiment
            sentiment_aggregator: Agent to aggregate sentiment data
            signal_decision_agent: Optional agent to generate trading signals
        """
        
        async def process_story_through_pipeline(headline: str, tickers: List[str], timestamp: str):
            """Process a single story through the sentiment analysis pipeline."""
            try:
                # Step 1: Classify headline sentiment (skipping ticker extraction)
                sentiment_data = await headline_classifier.process(headline)
                
                # Step 2: Aggregate sentiment for the provided tickers
                if tickers:
                    aggregated_data = await sentiment_aggregator.process((timestamp, sentiment_data, tickers))
                    
                    # Step 3: Generate trading signals (optional)
                    if signal_decision_agent and aggregated_data:
                        signals = await signal_decision_agent.process(aggregated_data)
                        self.logger.info(f"Generated signals for {headline[:50]}...: {list(signals.keys())}")
                    
                    self.logger.info(f"Processed story with tickers {tickers}: {headline[:50]}...")
                else:
                    self.logger.warning(f"No tickers provided for story: {headline[:50]}...")
                    
            except Exception as e:
                self.logger.error(f"Error in sentiment pipeline for story: {e}")
        
        # Set the processor
        self.set_story_processor(process_story_through_pipeline)
        
        # Start the continuous stream
        self.logger.info(f"Starting TickerTick news stream with {self.fetch_interval_seconds}s interval")
        
        while True:
            try:
                await self.process()
                await asyncio.sleep(self.fetch_interval_seconds)
            except Exception as e:
                self.logger.error(f"Error in news stream loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def get_latest_stories(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the latest stories without processing them through the pipeline."""
        return await self.fetcher.fetch_latest_news(limit=limit)
    
    def get_api_usage_info(self) -> Dict[str, Any]:
        """Get API usage information."""
        return self.fetcher.get_api_usage_info()
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the news agent."""
        return {
            "fetch_interval_seconds": self.fetch_interval_seconds,
            "processed_stories_count": len(self.processed_story_ids),
            "max_processed_ids": self.max_processed_ids,
            "api_usage": self.get_api_usage_info(),
            "has_story_processor": self.story_processor is not None
        }

# Example usage and integration
if __name__ == "__main__":
    import sys
    import os
    
    # Add the agents directory to path for imports
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from headline_classifier_agent import HeadlineClassifierAgent
    from sentiment_aggregator_agent import SentimentAggregatorAgent
    from signal_decision_agent import SignalDecisionAgent
    
    async def test_tickertick_news_agent():
        print("Testing TickerTick News Agent Integration")
        print("=" * 50)
        
        # Initialize agents
        news_agent = TickerTickNewsAgent(fetch_interval_seconds=120)  # 2 minutes for testing
        headline_classifier = HeadlineClassifierAgent()
        sentiment_aggregator = SentimentAggregatorAgent(window_minutes=10)
        signal_decision = SignalDecisionAgent()
        
        # Test 1: Get latest stories
        print("\n1. Testing latest stories fetch...")
        stories = await news_agent.get_latest_stories(limit=5)
        print(f"Fetched {len(stories)} stories")
        
        for i, story in enumerate(stories[:3], 1):
            print(f"\n{i}. {story['headline']}")
            print(f"   Tickers: {story['tickers']}")
            print(f"   Source: {story['source']}")
        
        # Test 2: Process stories through pipeline manually
        print(f"\n2. Testing pipeline processing...")
        
        if stories:
            test_story = stories[0]
            headline = test_story["headline"]
            tickers = test_story["tickers"]
            timestamp = test_story["timestamp"]
            
            print(f"Processing: {headline}")
            print(f"Tickers: {tickers}")
            
            # Step 1: Sentiment classification
            sentiment_data = await headline_classifier.process(headline)
            print(f"Sentiment: {sentiment_data}")
            
            # Step 2: Sentiment aggregation (note: tickers already provided!)
            if tickers:
                aggregated_data = await sentiment_aggregator.process((timestamp, sentiment_data, tickers))
                print(f"Aggregated sentiment: {aggregated_data}")
                
                # Step 3: Signal generation
                if aggregated_data:
                    signals = await signal_decision.process(aggregated_data)
                    print(f"Trading signals: {signals}")
        
        # Test 3: Status check
        print(f"\n3. Agent status:")
        status = news_agent.get_status()
        print(f"Status: {status}")
        
        print(f"\n4. Testing short stream (30 seconds)...")
        
        # Test a short stream
        async def short_stream_test():
            count = 0
            original_interval = news_agent.fetch_interval_seconds
            news_agent.fetch_interval_seconds = 35  # 35 seconds for testing
            
            async def limited_processor(headline, tickers, timestamp):
                nonlocal count
                count += 1
                print(f"Stream processed story {count}: {headline[:50]}... [{', '.join(tickers)}]")
                if count >= 2:  # Process max 2 stories
                    return
            
            news_agent.set_story_processor(limited_processor)
            
            try:
                await asyncio.wait_for(news_agent.process(), timeout=40)
                print(f"Short stream test completed, processed {count} stories")
            except asyncio.TimeoutError:
                print("Stream test timeout (expected)")
            finally:
                news_agent.fetch_interval_seconds = original_interval
        
        await short_stream_test()
        
        print("\n" + "=" * 50)
        print("TickerTick News Agent test completed!")
    
    asyncio.run(test_tickertick_news_agent()) 