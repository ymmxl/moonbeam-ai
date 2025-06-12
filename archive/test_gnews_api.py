#!/usr/bin/env python3
"""
Test script to debug the GNews API integration
"""

import asyncio
import logging
from gnews_fetcher import GNewsFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestGNewsAPI")

async def test_latest_news():
    """Test the latest news endpoint logic"""
    
    print("🚀 Testing GNews API Integration")
    print("=" * 50)
    
    # Test GNews Fetcher
    api_key = "9e3d18b39f07ccfbf9ece36d214188eb"
    fetcher = GNewsFetcher(api_key)
    
    print("\n📰 Fetching latest news...")
    try:
        news_articles = await fetcher.fetch_latest_news()
        
        print(f"✅ Fetched {len(news_articles)} articles")
        
        for i, article in enumerate(news_articles[:3], 1):
            print(f"\n{i}. {article['headline']}")
            print(f"   Description: {article['description'][:100]}...")
            print(f"   Source: {article['source']['name']}")
            print(f"   URL: {article['url']}")
            print(f"   Published: {article['published_at']}")
        
        # Test the return format for the API
        api_response = {
            "success": True,
            "articles": news_articles,
            "count": len(news_articles)
        }
        
        print(f"\n📊 API Response structure valid: {bool(api_response['success'])}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_latest_news()) 