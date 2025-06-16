#!/usr/bin/env python3
import asyncio
from gnews_fetcher import GNewsFetcher

async def test():
    fetcher = GNewsFetcher('9e3d18b39f07ccfbf9ece36d214188eb')
    # Reset the processed articles cache
    fetcher.processed_articles = set()
    news = await fetcher.fetch_latest_news()
    print(f'Found {len(news)} articles')
    for i, article in enumerate(news[:2], 1):
        print(f'{i}. {article["headline"]}')

if __name__ == "__main__":
    asyncio.run(test()) 