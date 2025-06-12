#!/usr/bin/env python3
"""
Test script for Alpha Vantage integration with moonbeamAI
"""

import asyncio
import logging
from alpha_vantage_news_fetcher import AlphaVantageNewsFetcher
from system_coordinator import SystemCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestAlphaVantage")

async def test_alpha_vantage_integration():
    """Test the Alpha Vantage integration."""
    
    # Configuration
    API_KEY = "42UELCP2HWG56JHF"
    
    print("🚀 Testing Alpha Vantage Integration for moonbeamAI")
    print("=" * 50)
    
    # Test 1: News Fetcher
    print("\n📰 Test 1: Alpha Vantage News Fetcher")
    try:
        news_fetcher = AlphaVantageNewsFetcher(API_KEY)
        print(f"✅ News fetcher initialized with API key: {API_KEY[:8]}...")
        
        # Get API usage info
        usage_info = news_fetcher.get_api_usage_info()
        print(f"📊 API Usage Info: {usage_info}")
        
        # Fetch latest news
        print("🔄 Fetching latest news...")
        headlines = await news_fetcher.fetch_latest_news()
        print(f"📈 Fetched {len(headlines)} headlines")
        
        for i, headline in enumerate(headlines[:3], 1):
            print(f"  {i}. {headline}")
            
    except Exception as e:
        print(f"❌ News fetcher test failed: {e}")
        return False
    
    # Test 2: System Coordinator with Alpha Vantage
    print("\n🤖 Test 2: System Coordinator with Alpha Vantage")
    try:
        coordinator = SystemCoordinator(
            alpha_vantage_api_key=API_KEY,
            use_alpha_vantage_sentiment=True
        )
        print("✅ System coordinator initialized with Alpha Vantage support")
        
        # Get system status
        status = await coordinator.get_system_status()
        print(f"📊 System Status: {status}")
        
        # Test processing a headline
        if headlines:
            test_headline = headlines[0]
            print(f"🧪 Testing headline processing: {test_headline[:50]}...")
            
            signals = await coordinator.process_headline(test_headline)
            print(f"📈 Generated {len(signals)} trading signals")
            
            for ticker, signal_data in signals.items():
                print(f"  {ticker}: {signal_data}")
        
    except Exception as e:
        print(f"❌ System coordinator test failed: {e}")
        return False
    
    # Test 3: Enhanced Sentiment Analysis
    print("\n💭 Test 3: Enhanced Sentiment Analysis")
    try:
        # Test with a few sample headlines
        test_headlines = [
            "Apple reports record quarterly earnings, stock surges 15%",
            "Tesla faces recall over safety concerns, shares plummet",
            "Microsoft announces new cloud partnership with Google"
        ]
        
        for headline in test_headlines:
            print(f"\nTesting: {headline}")
            sentiment = await coordinator.headline_classifier.run(headline)
            print(f"  Sentiment: {sentiment.get('sentiment', 'N/A')}")
            print(f"  Confidence: {sentiment.get('confidence', 'N/A')}")
            print(f"  Method: {sentiment.get('method', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Sentiment analysis test failed: {e}")
        return False
    
    print("\n✅ All tests completed successfully!")
    print("\n🎯 Alpha Vantage integration is ready for moonbeamAI")
    print("\nNext steps:")
    print("1. Run the app: python app.py")
    print("2. Visit http://localhost:8000 to see the web interface")
    print("3. Check /system-status endpoint for real-time status")
    print("4. Use /fetch-news endpoint to manually trigger news fetching")
    
    return True

async def test_news_stream():
    """Test the news stream functionality (short test)."""
    print("\n🔄 Testing news stream (30 seconds)...")
    
    API_KEY = "42UELCP2HWG56JHF"
    news_fetcher = AlphaVantageNewsFetcher(API_KEY)
    coordinator = SystemCoordinator(
        alpha_vantage_api_key=API_KEY,
        use_alpha_vantage_sentiment=True
    )
    
    processed_count = 0
    
    async def headline_processor(headline):
        nonlocal processed_count
        processed_count += 1
        print(f"📰 Processing headline {processed_count}: {headline[:50]}...")
        
        signals = await coordinator.process_headline(headline)
        if signals:
            print(f"  → Generated signals for: {list(signals.keys())}")
        else:
            print("  → No trading signals generated")
    
    # Run for 30 seconds
    print("🕒 Running news stream for 30 seconds...")
    try:
        await asyncio.wait_for(
            news_fetcher.start_stream(headline_processor, interval_seconds=30),
            timeout=35
        )
    except asyncio.TimeoutError:
        print(f"✅ Stream test completed. Processed {processed_count} headlines.")

if __name__ == "__main__":
    print("Alpha Vantage Integration Test for moonbeamAI")
    print("Choose test to run:")
    print("1. Basic integration test")
    print("2. News stream test (30 seconds)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_alpha_vantage_integration())
    elif choice == "2":
        asyncio.run(test_news_stream())
    else:
        print("Invalid choice. Running basic integration test...")
        asyncio.run(test_alpha_vantage_integration()) 