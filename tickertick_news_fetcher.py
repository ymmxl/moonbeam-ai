import asyncio
import aiohttp
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Callable, Awaitable, Optional
import time
import sys

class TickerTickNewsFetcher:
    """
    Fetches financial news using the TickerTick API.
    Respects the 10 requests per minute rate limit.
    """
    
    def __init__(self):
        self.base_url = "https://api.tickertick.com"
        self.logger = logging.getLogger("TickerTickNewsFetcher")
        
        # Rate limiting: 10 requests per minute
        self.max_requests_per_minute = 10
        self.request_timestamps = []
        
        # Track last story ID for pagination to avoid duplicates
        self.last_story_id = None
        
        # Story types to fetch (prioritize curated news)
        self.story_types = ["T:curated", "T:market", "T:analysis", "T:earning"]
        self.top_50_tickers = [
    "tt:aapl",   # Apple Inc.
    "tt:msft",   # Microsoft Corporation
    "tt:amzn",   # Amazon.com Inc.
    "tt:googl",  # Alphabet Inc. (Class A)
    "tt:goog",   # Alphabet Inc. (Class C)
    "tt:tsla",   # Tesla Inc.
    "tt:meta",   # Meta Platforms Inc.
    "tt:nvda",   # NVIDIA Corporation
    "tt:nflx",   # Netflix Inc.
    "tt:orcl",   # Oracle Corporation
    "tt:crm",    # Salesforce Inc.
    "tt:adbe",   # Adobe Inc.
    "tt:intc",   # Intel Corporation
    "tt:amd",    # Advanced Micro Devices
    "tt:csco",   # Cisco Systems Inc.
    "tt:ibm",    # International Business Machines
    "tt:jpm",    # JPMorgan Chase & Co.
    "tt:bac",    # Bank of America Corporation
    "tt:wfc",    # Wells Fargo & Company
    "tt:gs",     # Goldman Sachs Group Inc.
    "tt:ms",     # Morgan Stanley
    "tt:c",      # Citigroup Inc.
    "tt:v",      # Visa Inc.
    "tt:ma",     # Mastercard Incorporated
    "tt:pypl",   # PayPal Holdings Inc.
    "tt:jnj",    # Johnson & Johnson
    "tt:pfizer", # Pfizer Inc.
    "tt:abbv",   # AbbVie Inc.
    "tt:mrk",    # Merck & Co. Inc.
    "tt:unh",    # UnitedHealth Group Inc.
    "tt:xom",    # Exxon Mobil Corporation
    "tt:cvx",    # Chevron Corporation
    "tt:cop",    # ConocoPhillips
    "tt:ko",     # The Coca-Cola Company
    "tt:pep",    # PepsiCo Inc.
    "tt:wmt",    # Walmart Inc.
    "tt:hd",     # The Home Depot Inc.
    "tt:pg",     # Procter & Gamble Company
    "tt:jmia",   # Jumia Technologies AG
    "tt:dis",    # The Walt Disney Company
    "tt:nke",    # NIKE Inc.
    "tt:mcd",    # McDonald's Corporation
    "tt:sbux",   # Starbucks Corporation
    "tt:ba",     # The Boeing Company
    "tt:cat",    # Caterpillar Inc.
    "tt:ge",     # General Electric Company
    "tt:f",      # Ford Motor Company
    "tt:gm",     # General Motors Company
    "tt:spy",    # SPDR S&P 500 ETF Trust
    "tt:qqq"     # Invesco QQQ Trust
]
        self.interval = 120 #seconds
        self.limit = 50

    def _can_make_request(self) -> bool:
        """Check if we can make a request without hitting rate limits."""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 60
        ]
        
        return len(self.request_timestamps) < self.max_requests_per_minute
    
    def _record_request(self):
        """Record that we made a request."""
        self.request_timestamps.append(time.time())
    
    def _wait_time_for_next_request(self) -> float:
        """Calculate how long to wait before next request."""
        if self._can_make_request():
            return 0
        
        # Find the oldest timestamp and calculate wait time
        if self.request_timestamps:
            oldest_timestamp = min(self.request_timestamps)
            wait_time = 60 - (time.time() - oldest_timestamp) + 1  # +1 for safety
            return max(0, wait_time)
        
        return 0
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make a rate-limited request to the TickerTick API."""
        wait_time = self._wait_time_for_next_request()
        if wait_time > 0:
            self.logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds...")
            await asyncio.sleep(wait_time)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers={"content-type": "application/json"}) as response:
                    if response.status == 429:
                        self.logger.warning("Hit rate limit, waiting 60 seconds...")
                        await asyncio.sleep(60)
                        return None
                    
                    if response.status == 200:
                        self._record_request()
                        return await response.json()
                    else:
                        self.logger.error(f"API request failed with status {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error making request to {url}: {e}")
            return None
    
    
    async def fetch_latest_news(self, lookback_hours: int = 16) -> List[Dict[str, Any]]:
        """
        Fetch the latest news stories from TickerTick API.
        
        Args:
            lookback_hours: Only return news from the last N hours (default: 16)
            
        Returns:
            List of news stories with ticker information
        """
        tickers = ' '.join(self.top_50_tickers)
        params = {
            "q": f"(and (or {tickers}) T:curated)",
            "n": min(self.limit,1000)  # API max is 1000
        }

        # Add pagination if we have a last story ID
        if self.last_story_id:
            params["last"] = self.last_story_id
        
        response = await self._make_request("/feed", params)
        
        if not response or "stories" not in response:
            self.logger.warning("No stories received from TickerTick API")
            return []
        
        stories = response["stories"]

        
        # Update last story ID for pagination
        if stories and "last_id" in response:
            self.last_story_id = response["last_id"]
        
        # Calculate cutoff time for lookback period
        from datetime import timedelta
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        cutoff_timestamp_ms = cutoff_time.timestamp() * 1000
        
        # Convert to our internal format
        formatted_stories = []
        for story in stories:
            # Convert timestamp from milliseconds to ISO format
            timestamp_ms = story.get("time", 0)
            
            # Skip stories older than the lookback period
            if timestamp_ms < cutoff_timestamp_ms:
                continue
                
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat()
            
            formatted_story = {
                "id": story.get("id"),
                "headline": story.get("title", ""),
                "url": story.get("url", ""),
                "source": story.get("source", ""),
                "timestamp": timestamp,
                "tickers": story.get("tickers", []),  # This is the key field!
                "description": story.get("description", ""),
                "tags": story.get("tags", [])
            }
            
            # Only include stories that have tickers
            if formatted_story["tickers"] and formatted_story["headline"]:
                formatted_stories.append(formatted_story)
        
        self.logger.info(f"Fetched {len(formatted_stories)} stories with tickers (lookback: {lookback_hours}h)")
        return formatted_stories
    
    async def start_stream(self, callback: Callable[[List[Dict[str, Any]]], Awaitable[None]], lookback_hours: int = 16):
        """
        Start streaming news stories at the specified interval.
        
        Args:
            callback: Async function to call with list of news stories
            lookback_hours: Only fetch news from the last N hours (default: 16)
        """
        # Ensure interval is at least 60 seconds to respect rate limits
        if self.interval < 60:
            self.logger.warning(f"Interval {self.interval}s is too short, using 60s minimum")
            self.interval = 60
        
        self.logger.info(f"Starting TickerTick news stream with {self.interval}s interval, {lookback_hours}h lookback")
        
        while True:
            try:
                # Fetch news stories with lookback period
                stories = await self.fetch_latest_news(lookback_hours=lookback_hours)
                
                if stories:
                    await callback(stories)
                else:
                    self.logger.info("No new stories found")
                
            except Exception as e:
                self.logger.error(f"Error in news stream: {e}")
            
            # Wait for next fetch
            await asyncio.sleep(self.interval)
    
    def get_api_usage_info(self) -> Dict[str, Any]:
        """Get information about API usage."""
        current_time = time.time()
        
        # Count recent requests
        recent_requests = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 60
        ]
        
        return {
            "requests_in_last_minute": len(recent_requests),
            "max_requests_per_minute": self.max_requests_per_minute,
            "can_make_request": self._can_make_request(),
            "wait_time_seconds": self._wait_time_for_next_request(),
            "total_requests_made": len(self.request_timestamps)
        }

# Example usage and testing
if __name__ == "__main__":
    async def test_fetcher():
        fetcher = TickerTickNewsFetcher()
        
        print("Testing TickerTick News Fetcher...")
        print("=" * 50)
        
        # Test API usage info
        usage = fetcher.get_api_usage_info()
        print(f"API Usage: {usage}")
        
        # Test fetching news
        print("\nFetching latest news...")
        stories = await fetcher.fetch_latest_news()
        
        print(f"\nFetched {len(stories)} stories:")
        for i, story in enumerate(stories[:3], 1):
            print(f"\n{i}. {story['headline']}")
            print(f"   Source: {story['source']}")
            print(f"   Tickers: {story['tickers']}")
            print(f"   Timestamp: {story['timestamp']}")
        
        # Test rate limiting
        print(f"\nAfter fetching, usage: {fetcher.get_api_usage_info()}")
    
    # For testing a short stream
    async def test_stream():
        fetcher = TickerTickNewsFetcher()
        
        async def process_stories(stories):
            print(f"Stream received {len(stories)} stories")
            for story in stories[:2]:
                print(f"  - {story['headline']} [{', '.join(story['tickers'])}.upper()]")
        
        # Run for just 2 iterations for testing
        count = 0
        async def limited_callback(stories):
            nonlocal count
            count += 1
            await process_stories(stories)
            if count >= 2:
                return
        
        print("\nTesting stream (2 iterations)...")
        try:
            await asyncio.wait_for(
                fetcher.start_stream(limited_callback), 
                timeout=150
            )
        except asyncio.TimeoutError:
            print("Stream test completed")
    
    asyncio.run(test_fetcher())
    print("\n" + "=" * 50)
    asyncio.run(test_stream()) 