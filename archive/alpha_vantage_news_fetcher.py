import asyncio
import logging
import requests
import time
from datetime import datetime
from typing import List, Callable, Awaitable, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AlphaVantageNewsFetcher")

class AlphaVantageNewsFetcher:
    """
    Fetches real financial news from Alpha Vantage API.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.last_fetch_time = None
        self.processed_articles = set()  # Track processed articles to avoid duplicates
        
        # Popular financial tickers to fetch news for
        self.financial_tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "JPM", "BAC", "WMT", "DIS", "KO", "INTC", "AMD", "IBM",
            "GS", "V", "MA", "JNJ", "PG", "UNH", "HD", "CVX"
        ]
        
        # Track which ticker we're currently fetching (rotate through them)
        self.current_ticker_index = 0
    
    def _get_market_news(self) -> List[Dict[str, Any]]:
        """
        Fetch general market news from Alpha Vantage.
        
        Returns:
            List of news articles
        """
        try:
            params = {
                'function': 'NEWS_SENTIMENT',
                'topics': 'financial_markets,economy_macro,technology',
                'apikey': self.api_key,
                'limit': 50,  # Get up to 20 articles
                'sort': 'LATEST'
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'feed' in data:
                return data['feed']
            else:
                logger.warning(f"Unexpected response format: {data}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching market news: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing market news response: {e}")
            return []
    
    def _get_ticker_news(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Fetch news for a specific ticker from Alpha Vantage.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            List of news articles for the ticker
        """
        try:
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': ticker,
                'apikey': self.api_key,
                'limit': 10,  # Get up to 10 articles per ticker
                'sort': 'LATEST'
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'feed' in data:
                return data['feed']
            else:
                logger.warning(f"Unexpected response format for {ticker}: {data}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching news for {ticker}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing news response for {ticker}: {e}")
            return []
    
    def _extract_headline_from_article(self, article: Dict[str, Any]) -> str:
        """
        Extract a clean headline from an Alpha Vantage news article.
        
        Args:
            article: News article data from Alpha Vantage
            
        Returns:
            Clean headline string
        """
        headline = article.get('title', '')
        
        # Clean up the headline
        headline = headline.strip()
        
        # Add source information if available
        source = article.get('source', '')
        if source:
            headline = f"{headline} (via {source})"
        
        return headline
    
    def _is_recent_article(self, article: Dict[str, Any], max_age_hours: int = 1) -> bool:
        """
        Check if an article is recent enough to process.
        
        Args:
            article: News article data
            max_age_hours: Maximum age in hours
            
        Returns:
            True if article is recent enough
        """
        try:
            time_published = article.get('time_published', '')
            if not time_published:
                return False
            
            # Parse Alpha Vantage timestamp format: YYYYMMDDTHHMMSS
            article_time = datetime.strptime(time_published, '%Y%m%dT%H%M%S')
            current_time = datetime.now()
            
            age_hours = (current_time - article_time).total_seconds() / 3600
            return age_hours <= max_age_hours
            
        except Exception as e:
            logger.warning(f"Error parsing article timestamp: {e}")
            return True  # If we can't parse, assume it's recent
    
    def _get_unique_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out articles we've already processed.
        
        Args:
            articles: List of news articles
            
        Returns:
            List of unprocessed articles
        """
        unique_articles = []
        
        for article in articles:
            article_id = article.get('url', '') or article.get('title', '')
            if article_id and article_id not in self.processed_articles:
                unique_articles.append(article)
                self.processed_articles.add(article_id)
        
        return unique_articles
    
    async def fetch_latest_news(self) -> List[str]:
        """
        Fetch the latest financial news headlines.
        
        Returns:
            List of news headlines
        """
        headlines = []
        
        try:
            # Alternate between general market news and ticker-specific news
            if self.current_ticker_index == 0:
                logger.info("Fetching general market news...")
                articles = self._get_market_news()
            else:
                # Get news for a specific ticker (rotate through our list)
                ticker_index = (self.current_ticker_index - 1) % len(self.financial_tickers)
                ticker = self.financial_tickers[ticker_index]
                logger.info(f"Fetching news for ticker: {ticker}")
                articles = self._get_ticker_news(ticker)
            
            # Move to next ticker for next fetch
            self.current_ticker_index = (self.current_ticker_index + 1) % (len(self.financial_tickers) + 1)
            
            if not articles:
                logger.warning("No articles received from Alpha Vantage")
                return headlines
            
            # Filter for recent and unique articles
            recent_articles = [article for article in articles if self._is_recent_article(article)]
            unique_articles = self._get_unique_articles(recent_articles)
            
            # Extract headlines
            for article in unique_articles:
                headline = self._extract_headline_from_article(article)
                if headline:
                    headlines.append(headline)
            
            logger.info(f"Fetched {len(headlines)} new headlines from Alpha Vantage")
            
        except Exception as e:
            logger.error(f"Error fetching news from Alpha Vantage: {e}")
        
        return headlines
    
    async def start_stream(self, callback: Callable[[str], Awaitable[None]], interval_seconds: float = 600):
        """
        Start streaming news headlines at the specified interval.
        
        Args:
            callback: Async function to call with each headline
            interval_seconds: Interval between news fetches in seconds (default 10 minutes)
        """
        logger.info(f"Starting Alpha Vantage news stream with {interval_seconds}s intervals")
        
        while True:
            try:
                headlines = await self.fetch_latest_news()
                
                # Process each headline
                for headline in headlines:
                    try:
                        await callback(headline)
                        # Small delay between headlines to avoid overwhelming the system
                        await asyncio.sleep(1)
                    except Exception as e:
                        logger.error(f"Error processing headline '{headline}': {e}")
                
                # Wait for the next fetch interval
                logger.info(f"Processed {len(headlines)} headlines. Waiting {interval_seconds}s for next fetch...")
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in news stream: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    def get_api_usage_info(self) -> Dict[str, Any]:
        """
        Get information about API usage limits.
        
        Returns:
            API usage information
        """
        return {
            "api_key": self.api_key[:8] + "...",  # Partially masked key
            "daily_limit": 500,  # Alpha Vantage free tier limit
            "rate_limit": "5 calls per minute",
            "documentation": "https://www.alphavantage.co/documentation/"
        } 