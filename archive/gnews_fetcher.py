import asyncio
import logging
import requests
import time
import re
from datetime import datetime, timedelta
from typing import List, Callable, Awaitable, Dict, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GNewsAPI")

class GNewsFetcher:
    """
    Fetches real financial news from GNews API.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://gnews.io/api/v4"
        self.last_fetch_time = None
        self.processed_articles = set()  # Track processed articles to avoid duplicates
        
        # Financial keywords for search
        self.financial_keywords = [
            "stock market", "finance", "trading", "investment", "economy", 
            "earnings", "IPO", "merger", "acquisition", "cryptocurrency",
            "bitcoin", "ethereum", "nasdaq", "dow jones", "s&p 500",
            "federal reserve", "interest rates", "inflation", "gdp"
        ]
        
        # Major financial companies and stocks
        self.major_stocks = [
            "Apple", "Microsoft", "Google", "Amazon", "Tesla", "Meta", 
            "NVIDIA", "Netflix", "JPMorgan", "Bank of America", "Walmart", 
            "Disney", "Coca-Cola", "Intel", "AMD", "IBM", "Goldman Sachs", 
            "Visa", "Mastercard", "Johnson & Johnson", "Procter & Gamble"
        ]
        
        # Track which keyword we're currently using (rotate through them)
        self.current_keyword_index = 0
    
    def _build_search_query(self) -> str:
        """Build a search query for financial news."""
        # Rotate through financial keywords and major stocks
        all_terms = self.financial_keywords + self.major_stocks
        current_term = all_terms[self.current_keyword_index % len(all_terms)]
        self.current_keyword_index += 1
        return current_term
    
    def _get_financial_news(self, query: str = None, max_articles: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch financial news from GNews API.
        
        Args:
            query: Search query (if None, uses default financial terms)
            max_articles: Maximum number of articles to fetch
            
        Returns:
            List of news articles
        """
        try:
            if not query:
                query = self._build_search_query()
            
            params = {
                'q': query,
                'lang': 'en',
                'country': 'us',
                'max': min(max_articles, 10),  # GNews API limit is 10 per request
                'apikey': self.api_key
            }
            
            # Add time filter for recent articles (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            params['from'] = yesterday.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            response = requests.get(f"{self.base_url}/search", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'articles' in data:
                logger.info(f"Fetched {len(data['articles'])} articles for query: '{query}'")
                return data['articles']
            else:
                logger.warning(f"Unexpected response format: {data}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching news for '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing news response for '{query}': {e}")
            return []
    
    def _get_top_headlines(self, category: str = "business") -> List[Dict[str, Any]]:
        """
        Fetch top headlines from GNews API.
        
        Args:
            category: News category (business, technology, etc.)
            
        Returns:
            List of news articles
        """
        try:
            params = {
                'category': category,
                'lang': 'en',
                'country': 'us',
                'max': 10,
                'apikey': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/top-headlines", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'articles' in data:
                logger.info(f"Fetched {len(data['articles'])} top headlines for category: '{category}'")
                return data['articles']
            else:
                logger.warning(f"Unexpected response format: {data}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching top headlines for '{category}': {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing top headlines response for '{category}': {e}")
            return []
    
    def _extract_news_data_from_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured news data from a GNews article.
        
        Args:
            article: News article data from GNews
            
        Returns:
            Structured news data with headline, description, content, etc.
        """
        return {
            'headline': article.get('title', '').strip(),
            'description': article.get('description', '').strip(),
            'content': article.get('content', '').strip(),
            'url': article.get('url', ''),
            'image': article.get('image', ''),
            'published_at': article.get('publishedAt', ''),
            'source': {
                'name': article.get('source', {}).get('name', ''),
                'url': article.get('source', {}).get('url', '')
            }
        }
    
    def _is_recent_article(self, article: Dict[str, Any], max_age_hours: int = 24) -> bool:
        """
        Check if an article is recent enough to process.
        
        Args:
            article: News article data
            max_age_hours: Maximum age in hours
            
        Returns:
            True if article is recent enough
        """
        try:
            published_at = article.get('publishedAt', '')
            if not published_at:
                return False
            
            # Parse GNews timestamp format: ISO 8601
            article_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            current_time = datetime.now(article_time.tzinfo)
            
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
    
    def _is_financial_relevant(self, article: Dict[str, Any]) -> bool:
        """
        Check if an article is relevant to financial trading.
        
        Args:
            article: News article data
            
        Returns:
            True if article is financially relevant
        """
        text_to_check = f"{article.get('title', '')} {article.get('description', '')}".lower()
        
        # More comprehensive financial terms
        financial_terms = [
            'stock', 'share', 'trading', 'market', 'finance', 'financial', 'investment', 
            'earnings', 'revenue', 'profit', 'loss', 'ipo', 'merger', 'acquisition', 
            'dividend', 'nasdaq', 'nyse', 'dow', 's&p', 'sp500', 'russell',
            'cryptocurrency', 'crypto', 'bitcoin', 'ethereum', 'blockchain',
            'fed', 'federal reserve', 'interest rate', 'inflation', 'gdp', 
            'economy', 'economic', 'recession', 'growth', 'unemployment',
            'bank', 'banking', 'credit', 'debt', 'loan', 'mortgage',
            'currency', 'dollar', 'euro', 'yen', 'forex', 'exchange',
            'commodity', 'oil', 'gold', 'silver', 'futures', 'options',
            'bond', 'treasury', 'yield', 'valuation', 'analyst',
            'quarter', 'quarterly', 'annual', 'guidance', 'forecast',
            'ceo', 'cfo', 'executive', 'board', 'shareholder',
            # Company names and sectors
            'apple', 'microsoft', 'google', 'amazon', 'tesla', 'meta',
            'nvidia', 'netflix', 'disney', 'walmart', 'jpmorgan',
            'technology', 'tech', 'healthcare', 'pharma', 'energy',
            'retail', 'automotive', 'aerospace', 'defense', 'utilities'
        ]
        
        # Check if any financial term is present
        if any(term in text_to_check for term in financial_terms):
            return True
        
        # For business category, be more lenient
        category_keywords = ['business', 'corporate', 'company', 'enterprise', 'industry']
        if any(keyword in text_to_check for keyword in category_keywords):
            return True
        
        # Check for stock ticker patterns (like AAPL, MSFT, etc.)
        ticker_pattern = r'\b[A-Z]{1,5}\b'  # 1-5 uppercase letters
        if re.search(ticker_pattern, article.get('title', '')):
            return True
        
        return False
    
    async def fetch_latest_news(self) -> List[Dict[str, Any]]:
        """
        Fetch the latest financial news articles with full data.
        
        Returns:
            List of structured news data dictionaries
        """
        all_news = []
        
        try:
            # Alternate between search and top headlines
            if self.current_keyword_index % 3 == 0:
                # Get top business headlines
                logger.info("Fetching top business headlines...")
                articles = self._get_top_headlines("business")
            elif self.current_keyword_index % 3 == 1:
                # Get top technology headlines (often includes tech stocks)
                logger.info("Fetching top technology headlines...")
                articles = self._get_top_headlines("technology")
            else:
                # Search for specific financial terms
                search_query = self._build_search_query()
                logger.info(f"Searching for financial news: '{search_query}'")
                articles = self._get_financial_news(search_query)
            
            if not articles:
                logger.warning("No articles received from GNews API")
                return all_news
            
            logger.info(f"Received {len(articles)} articles from GNews")
            
            # Filter for recent, unique, and financially relevant articles
            recent_articles = [article for article in articles if self._is_recent_article(article)]
            logger.info(f"Recent articles (within 24 hours): {len(recent_articles)}")
            
            unique_articles = self._get_unique_articles(recent_articles)
            logger.info(f"Unique articles: {len(unique_articles)}")
            
            relevant_articles = [article for article in unique_articles if self._is_financial_relevant(article)]
            logger.info(f"Financially relevant articles: {len(relevant_articles)}")
            
            # Debug: Show a sample of what we're getting
            if articles:
                sample_article = articles[0]
                logger.info(f"Sample article title: {sample_article.get('title', 'N/A')}")
                logger.info(f"Sample article description: {sample_article.get('description', 'N/A')[:100]}...")
                logger.info(f"Sample article published: {sample_article.get('publishedAt', 'N/A')}")
                logger.info(f"Sample article is recent: {self._is_recent_article(sample_article)}")
                logger.info(f"Sample article is relevant: {self._is_financial_relevant(sample_article)}")
            
            # Extract structured data from articles
            for article in relevant_articles:
                news_data = self._extract_news_data_from_article(article)
                if news_data['headline']:  # Only include articles with valid headlines
                    all_news.append(news_data)
            
            logger.info(f"Processed {len(all_news)} relevant financial news articles")
            
        except Exception as e:
            logger.error(f"Error fetching news from GNews API: {e}")
        
        return all_news
    
    async def fetch_headlines_only(self) -> List[str]:
        """
        Fetch only the headlines for compatibility with existing system.
        
        Returns:
            List of news headlines
        """
        news_data = await self.fetch_latest_news()
        return [item['headline'] for item in news_data if item['headline']]
    
    async def start_stream(self, callback: Callable[[str], Awaitable[None]], interval_seconds: float = 300):
        """
        Start streaming news headlines at the specified interval.
        
        Args:
            callback: Async function to call with each headline
            interval_seconds: Interval between news fetches in seconds (default 5 minutes)
        """
        logger.info(f"Starting GNews stream with {interval_seconds}s intervals")
        
        while True:
            try:
                headlines = await self.fetch_headlines_only()
                
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
            "daily_limit": "100-500 calls/day",  # GNews API limits vary by plan
            "rate_limit": "10 calls per minute",
            "documentation": "https://gnews.io/docs",
            "current_keyword_index": self.current_keyword_index
        }

# Example usage and testing
if __name__ == "__main__":
    async def test_gnews_fetcher():
        # Test with the provided API key
        api_key = "9e3d18b39f07ccfbf9ece36d214188eb"
        fetcher = GNewsFetcher(api_key)
        
        print("Testing GNews Fetcher...")
        print("=" * 50)
        
        # Test fetching latest news with full data
        print("\n📰 Fetching latest financial news...")
        news_data = await fetcher.fetch_latest_news()
        
        for i, item in enumerate(news_data[:3], 1):
            print(f"\n{i}. {item['headline']}")
            print(f"   Description: {item['description'][:100]}...")
            print(f"   Source: {item['source']['name']}")
            print(f"   Published: {item['published_at']}")
        
        # Test fetching headlines only
        print(f"\n📈 Fetching headlines only...")
        headlines = await fetcher.fetch_headlines_only()
        
        for i, headline in enumerate(headlines[:5], 1):
            print(f"{i}. {headline}")
        
        print(f"\n📊 API Usage Info: {fetcher.get_api_usage_info()}")
    
    asyncio.run(test_gnews_fetcher()) 