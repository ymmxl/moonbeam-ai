import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Callable, Awaitable, Dict, Any
from GoogleNews import GoogleNews

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GoogleNewsFetcher")

class GoogleNewsFetcher:
    """
    Fetches real financial news from Google News using the GoogleNews package.
    
    REFACTORED FEATURES:
    - Enhanced batch processing with systematic pagination using .page_at(y)
    - Fetches exactly N articles per batch (default: 30)
    - Iterates through all available pages until target count is reached
    - Improved WebSocket streaming using new batch processing
    - Maintains backward compatibility with legacy methods
    - Ready for future integration with classifier agents
    
    METHODS:
    - fetch_batch_news(): New primary method for batch processing with pagination
    - fetch_headlines_batch(): Convenient method for getting headlines only
    - start_stream(): Updated to use batch processing
    - fetch_latest_news(): Legacy method (maintained for compatibility)
    - fetch_headlines_only(): Legacy method (maintained for compatibility)
    """
    
    def __init__(self, lang: str = 'en', region: str = 'US'):
        """
        Initialize the Google News fetcher.
        
        Args:
            lang: Language code (default: 'en')
            region: Region code (default: 'US')
        """
        self.gn = GoogleNews(lang=lang, region=region)
        self.last_fetch_time = None
        self.processed_articles = set()  # Track processed articles to avoid duplicates
        

        # Track which keyword we're currently using (rotate through them)
        self.current_keyword_index = 0
        self.total_fetches = 0
        self.total_articles_processed = 0
    
    def _build_search_query(self) -> str:
        """Build a search query for general financial news."""
        # Use broader financial terms to get general finance news
        general_finance_terms = [
            "financial news",
            "business news", 
            "stock market news",
            "economy news",
            "market news"
        ]
        current_term = ",".join(general_finance_terms)
        return current_term
    
    def _get_financial_news(self, query: str = None, max_articles: int = 10, period: str = '1d') -> List[Dict[str, Any]]:
        """
        Fetch financial news from Google News.
        
        Args:
            query: Search query (if None, uses default financial terms)
            max_articles: Maximum number of articles to fetch (GoogleNews returns 10 per page)
            period: Time period ('1h', '1d', '7d', '1m', '1y')
            
        Returns:
            List of news articles
        """
        try:
            if not query:
                query = self._build_search_query()
            
            # Clear previous results
            self.gn.clear()
            
            # Set time period for recent articles
            self.gn.set_period(period)
            
            # Perform search
            self.gn.search(query)
            
            # Get results
            results = self.gn.result()
            
            # If we need more articles, get additional pages
            if len(results) < max_articles and len(results) == 10:
                try:
                    self.gn.getpage(2)  # Get second page
                    page2_results = self.gn.result()
                    results.extend(page2_results[10:])  # Add only new results
                except Exception as e:
                    logger.debug(f"Could not fetch second page: {e}")
            
            logger.info(f"Fetched {len(results)} articles for query: '{query}'")
            return results[:max_articles]  # Limit to requested number
                
        except Exception as e:
            logger.error(f"Error fetching news for '{query}': {e}")
            return []
    
    def _extract_news_data_from_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured news data from a GoogleNews article.
        
        Args:
            article: News article data from GoogleNews
            
        Returns:
            Structured news data with headline, description, content, etc.
        """
        return {
            'headline': article.get('title', '').strip(),
            'description': article.get('desc', '').strip(),
            'content': article.get('desc', '').strip(),  # GoogleNews doesn't provide full content
            'url': article.get('link', ''),
            'image': article.get('img', ''),
            'published_at': article.get('date', ''),
            'datetime': article.get('datetime', ''),
            'source': {
                'name': article.get('media', ''),
                'url': article.get('link', '')
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
            # GoogleNews provides relative time descriptions
            date_str = article.get('date', '').lower()
            
            # Check for very recent articles
            if any(term in date_str for term in ['minute', 'hour', 'min ago', 'hr ago', 'hours ago', 'minutes ago']):
                return True
            
            # Check for today's articles
            if 'day ago' in date_str or 'today' in date_str:
                return max_age_hours >= 24
                
            # If we can't determine, assume it's recent enough
            return True
            
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
            # Use a combination of title and source as unique identifier
            article_id = f"{article.get('title', '')}_{article.get('media', '')}"
            if article_id and article_id not in self.processed_articles:
                unique_articles.append(article)
                self.processed_articles.add(article_id)
        
        return unique_articles
    
    def _is_financial_relevant(self, article: Dict[str, Any]) -> bool:
        """
        Check if an article is relevant to financial/business news.
        
        Args:
            article: News article data
            
        Returns:
            True if article appears to be financially relevant
        """
        title = article.get('title', '').lower()
        desc = article.get('desc', '').lower()
        text = f"{title} {desc}"
        
        # Financial keywords that indicate relevance
        financial_indicators = [
            'stock', 'market', 'trading', 'investment', 'finance', 'economic',
            'earnings', 'revenue', 'profit', 'loss', 'ipo', 'merger', 'acquisition',
            'cryptocurrency', 'bitcoin', 'crypto', 'nasdaq', 'dow', 's&p',
            'federal reserve', 'fed', 'interest rate', 'inflation', 'gdp',
            'business', 'company', 'corporation', 'shares', 'dividend',
            'analyst', 'forecast', 'quarter', 'fiscal', 'financial'
        ]
        
        return any(indicator in text for indicator in financial_indicators)
    
    async def fetch_latest_news(self) -> List[Dict[str, Any]]:
        """
        Fetch the latest financial news articles with full data.
        
        Returns:
            List of news articles with full data
        """
        try:
            # Get recent financial news
            articles = self._get_financial_news(period='1d', max_articles=50)
            
            if not articles:
                logger.warning("No articles fetched, trying broader search")
                # Try a broader search if no results
                articles = self._get_financial_news(query="financial news", period='1d', max_articles=10)
            
            # Filter for unique and recent articles
            unique_articles = self._get_unique_articles(articles)
            recent_articles = [article for article in unique_articles if self._is_recent_article(article)]
            relevant_articles = [article for article in recent_articles if self._is_financial_relevant(article)]
            
            # Convert to structured format
            structured_articles = []
            for article in relevant_articles:
                structured_article = self._extract_news_data_from_article(article)
                structured_articles.append(structured_article)
            
            self.total_fetches += 1
            self.total_articles_processed += len(structured_articles)
            self.last_fetch_time = datetime.now()
            
            logger.info(f"Processed {len(structured_articles)} relevant financial articles")
            return structured_articles
            
        except Exception as e:
            logger.error(f"Error fetching latest news: {e}")
            return []
    
    async def fetch_headlines_only(self) -> List[str]:
        """
        Fetch the latest financial news headlines only.
        
        Returns:
            List of news headlines
        """
        try:
            articles = await self.fetch_latest_news()
            headlines = [article['headline'] for article in articles if article.get('headline')]
            
            logger.info(f"Extracted {len(headlines)} headlines")
            return headlines
            
        except Exception as e:
            logger.error(f"Error fetching headlines: {e}")
            return []
    
    async def start_stream(self, callback: Callable[[str], Awaitable[None]], interval_seconds: float = 300, batch_size: int = 30):
        """
        Start a continuous stream of financial news headlines using batch processing.
        
        Args:
            callback: Async function to call with each headline
            interval_seconds: Seconds between fetches (default: 5 minutes)
            batch_size: Number of articles to fetch per batch (default: 30)
        """
        logger.info(f"Starting Google News stream with {interval_seconds}s intervals, batch size: {batch_size}")
        
        while True:
            try:
                # Use the new batch processing method
                batch_result = self.fetch_batch_news(batch_size=batch_size)
                articles = batch_result.get('articles', [])
                metadata = batch_result.get('batch_metadata', {})
                
                # Extract headlines from articles
                headlines = [article['headline'] for article in articles if article.get('headline')]
                
                # Process each headline through the callback
                for headline in headlines:
                    try:
                        await callback(headline)
                        await asyncio.sleep(0.1)  # Small delay between headlines
                    except Exception as e:
                        logger.warning(f"Error processing headline '{headline}': {e}")
                
                if headlines:
                    logger.info(f"Streamed {len(headlines)} headlines from {metadata.get('total_pages_fetched', 0)} pages")
                else:
                    logger.warning("No headlines fetched this cycle")
                    
                # Log batch metadata for monitoring
                if 'error' in metadata:
                    logger.error(f"Batch fetch error: {metadata['error']}")
                else:
                    logger.debug(f"Batch metadata: {metadata}")
                
                # Wait for next fetch cycle
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in news stream: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def fetch_headlines_batch(self, query: str = None, batch_size: int = 30, period: str = '1d') -> List[str]:
        """
        Fetch a batch of headlines only using the new pagination method.
        This method is designed for easy integration with classifier agents.
        
        Args:
            query: Search query (if None, uses default financial terms)
            batch_size: Target number of articles to fetch
            period: Time period ('1h', '1d', '7d', '1m', '1y')
            
        Returns:
            List of headlines
        """
        try:
            batch_result = self.fetch_batch_news(query=query, batch_size=batch_size, period=period)
            articles = batch_result.get('articles', [])
            headlines = [article['headline'] for article in articles if article.get('headline')]
            
            logger.info(f"Extracted {len(headlines)} headlines from batch")
            return headlines
            
        except Exception as e:
            logger.error(f"Error fetching headlines batch: {e}")
            return []

    def get_api_usage_info(self) -> Dict[str, Any]:
        """
        Get information about API usage (GoogleNews doesn't have usage limits).
        
        Returns:
            Dictionary with usage information
        """
        return {
            'service': 'Google News Fetch Count',
            'total_fetches': self.total_fetches,
            'total_articles_processed': self.total_articles_processed,
            'last_fetch_time': self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            'requires_api_key': False,
            'rate_limited': False,
            'cost': 'Free',
            'status': 'Active' if self.last_fetch_time else 'Not started'
        }

    def fetch_batch_news(self, query: str = None, batch_size: int = 30, period: str = '1d') -> Dict[str, Any]:
        """
        Fetch a batch of articles using systematic pagination.
        
        Args:
            query: Search query (if None, uses default financial terms)
            batch_size: Target number of articles to fetch
            period: Time period ('1h', '1d', '7d', '1m', '1y')
            
        Returns:
            Dictionary containing articles and batch metadata
        """
        try:
            if not query:
                query = self._build_search_query()
            
            # Clear previous results
            self.gn.clear()
            
            # Set time period for recent articles
            self.gn.set_period(period)
            
            # Perform initial search
            self.gn.search(query)
            
            all_articles = []
            page_number = 1
            max_pages = 10  # Safety limit to prevent infinite loops
            
            logger.info(f"Starting batch fetch for query: '{query}' (target: {batch_size} articles)")
            
            while len(all_articles) < batch_size and page_number <= max_pages:
                try:
                    if page_number == 1:
                        # First page is already loaded from search
                        results = self.gn.result()
                    else:
                        # Use page_at for subsequent pages
                        self.gn.get_page(page_number)
                        results = self.gn.result()
                    
                    # Check if we got new results
                    if not results or (page_number > 1 and len(results) == len(all_articles)):
                        logger.info(f"No more articles available after page {page_number - 1}")
                        break
                    
                    # For pages after the first, extract only new articles
                    if page_number == 1:
                        new_articles = results
                    else:
                        # Get only the new articles from this page
                        previous_count = (page_number - 1) * 10
                        new_articles = results[previous_count:] if len(results) > previous_count else []
                    
                    if not new_articles:
                        logger.info(f"No new articles found on page {page_number}")
                        break
                    
                    # Filter for unique articles
                    unique_new_articles = self._get_unique_articles(new_articles)
                    
                    # Add to our collection
                    all_articles.extend(unique_new_articles)
                    
                    logger.info(f"Page {page_number}: Found {len(unique_new_articles)} unique articles (total: {len(all_articles)})")
                    
                    page_number += 1
                    
                    # Small delay to be respectful to the service
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Error fetching page {page_number}: {e}")
                    break
            
            # Trim to exact batch size if we got more than requested
            if len(all_articles) > batch_size:
                all_articles = all_articles[:batch_size]
            
            # Filter for recent and financially relevant articles
            recent_articles = [article for article in all_articles if self._is_recent_article(article)]
            relevant_articles = [article for article in recent_articles if self._is_financial_relevant(article)]
            
            # Convert to structured format
            structured_articles = []
            for article in relevant_articles:
                structured_article = self._extract_news_data_from_article(article)
                structured_articles.append(structured_article)
            
            # Update tracking
            self.total_fetches += 1
            self.total_articles_processed += len(structured_articles)
            self.last_fetch_time = datetime.now()
            
            # Prepare batch metadata
            batch_metadata = {
                'total_pages_fetched': page_number - 1,
                'total_raw_articles': len(all_articles),
                'filtered_articles': len(structured_articles),
                'query_used': query,
                'period': period,
                'batch_size_requested': batch_size,
                'fetch_timestamp': self.last_fetch_time.isoformat()
            }
            
            logger.info(f"Batch fetch completed: {len(structured_articles)} relevant articles from {page_number - 1} pages")
            
            return {
                'articles': structured_articles,
                'batch_metadata': batch_metadata
            }
            
        except Exception as e:
            logger.error(f"Error in batch fetch for '{query}': {e}")
            return {
                'articles': [],
                'batch_metadata': {
                    'error': str(e),
                    'query_used': query,
                    'fetch_timestamp': datetime.now().isoformat()
                }
            }

# Test function
async def test_google_news_fetcher():
    """Test the Google News fetcher."""
    logger.info("Testing Google News Fetcher...")
    
    fetcher = GoogleNewsFetcher()
    
    # Test the new batch processing method
    print("Testing new batch processing method...")
    batch_result = fetcher.fetch_batch_news(batch_size=15)
    articles = batch_result.get('articles', [])
    metadata = batch_result.get('batch_metadata', {})
    
    print(f"Batch fetch results:")
    print(f"  - Fetched {len(articles)} articles")
    print(f"  - Pages processed: {metadata.get('total_pages_fetched', 0)}")
    print(f"  - Raw articles found: {metadata.get('total_raw_articles', 0)}")
    print(f"  - Query used: {metadata.get('query_used', 'N/A')}")
    
    if articles:
        print(f"\nSample article from batch:")
        article = articles[0]
        for key, value in article.items():
            print(f"  {key}: {value}")
    
    # # Test legacy methods for compatibility
    # print(f"\nTesting legacy methods...")
    # legacy_articles = await fetcher.fetch_latest_news()
    # print(f"Legacy fetch: {len(legacy_articles)} articles")
    
    # headlines = await fetcher.fetch_headlines_only()
    # print(f"Headlines only: {len(headlines)} headlines")
    
    # for i, headline in enumerate(headlines[:3]):
    #     print(f"  {i+1}. {headline}")
    
    # Test API usage info
    usage = fetcher.get_api_usage_info()
    print(f"\nAPI Usage Info: {usage}")
    
    # Test with different batch sizes
    # print(f"\nTesting different batch sizes:")
    # for batch_size in [5, 10]:
    #     batch_result = fetcher.fetch_batch_news(batch_size=batch_size)
    #     articles_count = len(batch_result.get('articles', []))
    #     pages_count = batch_result.get('batch_metadata', {}).get('total_pages_fetched', 0)
    #     print(f"  Batch size {batch_size}: Got {articles_count} articles from {pages_count} pages")

if __name__ == "__main__":
    asyncio.run(test_google_news_fetcher()) 