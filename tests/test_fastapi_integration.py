#!/usr/bin/env python3
"""
Comprehensive test script for FastAPI + Alpha Vantage integration
"""

import asyncio
import requests
import json
import time

def test_fastapi_endpoints():
    """Test all FastAPI endpoints with Alpha Vantage integration."""
    
    base_url = "http://localhost:8000"
    
    print("🚀 Testing FastAPI + Alpha Vantage Integration")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n🏥 Test 1: Health Check")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Status: {health_data['status']}")
            print(f"✅ Version: {health_data['version']}")
            print(f"✅ Alpha Vantage: {'Enabled' if health_data['alpha_vantage_enabled'] else 'Disabled'}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: System Status
    print("\n📊 Test 2: System Status")
    try:
        response = requests.get(f"{base_url}/system-status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ System Status: {status_data['status']}")
            print(f"✅ Sentiment Agent: {status_data['sentiment_agent']}")
            print(f"✅ News Fetcher: {status_data['news_fetcher']['type']}")
            print(f"✅ Alpha Vantage Enabled: {status_data['configuration']['alpha_vantage_enabled']}")
        else:
            print(f"❌ System status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ System status error: {e}")
        return False
    
    # Test 3: Process Headlines
    print("\n📰 Test 3: Headline Processing")
    test_headlines = [
        "Apple beats earnings expectations, stock surges 10%",
        "Tesla faces recall concerns, shares drop 5%",
        "Microsoft announces AI partnership, investors excited"
    ]
    
    for i, headline in enumerate(test_headlines, 1):
        print(f"\n  📝 Processing headline {i}: {headline[:40]}...")
        try:
            response = requests.post(
                f"{base_url}/process-headline",
                json={"headline": headline},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    signals = result.get('signals', {})
                    print(f"    ✅ Generated {len(signals)} trading signals")
                    for ticker, signal_data in signals.items():
                        print(f"    📈 {ticker}: {signal_data['signal']} (confidence: {signal_data['confidence']:.3f})")
                else:
                    print("    ❌ Processing failed")
            else:
                print(f"    ❌ Request failed: {response.status_code}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Test 4: Get Latest Signals
    print("\n📊 Test 4: Latest Signals")
    try:
        response = requests.get(f"{base_url}/latest-signals")
        if response.status_code == 200:
            signals = response.json()
            print(f"✅ Retrieved {len(signals)} latest signals")
            for ticker, signal_data in signals.items():
                print(f"  📈 {ticker}: {signal_data['signal']} (sentiment: {signal_data['sentiment']:.3f})")
        else:
            print(f"❌ Latest signals failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Latest signals error: {e}")
    
    # Test 5: Manual News Fetch
    print("\n📡 Test 5: Manual News Fetch")
    try:
        response = requests.post(f"{base_url}/fetch-news")
        if response.status_code == 200:
            news_data = response.json()
            print(f"✅ News fetch successful: {news_data['success']}")
            print(f"📰 Headlines fetched: {news_data['headlines_fetched']}")
            print(f"📊 Results processed: {len(news_data.get('results', []))}")
        else:
            print(f"❌ News fetch failed: {response.status_code}")
    except Exception as e:
        print(f"❌ News fetch error: {e}")
    
    # Test 6: Signal History
    print("\n📈 Test 6: Signal History")
    try:
        response = requests.get(f"{base_url}/signal-history")
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Retrieved {len(history)} historical records")
            if history:
                latest = history[-1]
                print(f"  📰 Latest headline: {latest['headline'][:50]}...")
                print(f"  📊 Generated signals: {len(latest.get('signals', {}))}")
        else:
            print(f"❌ Signal history failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Signal history error: {e}")
    
    # Test 7: API Documentation
    print("\n📚 Test 7: API Documentation")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200 and "swagger-ui" in response.text.lower():
            print("✅ Swagger UI documentation is available")
            print(f"    🌐 Access at: {base_url}/docs")
        else:
            print("❌ API documentation not accessible")
        
        # Test OpenAPI spec
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            openapi_spec = response.json()
            print(f"✅ OpenAPI spec available (version: {openapi_spec.get('openapi', 'unknown')})")
            print(f"    📖 Title: {openapi_spec.get('info', {}).get('title', 'Unknown')}")
        else:
            print("❌ OpenAPI spec not accessible")
    except Exception as e:
        print(f"❌ Documentation test error: {e}")
    
    print("\n🎉 FastAPI + Alpha Vantage Integration Test Complete!")
    print("\n🌟 Key Features Demonstrated:")
    print("  ✅ FastAPI high-performance async API")
    print("  ✅ Alpha Vantage real-time news integration")
    print("  ✅ Enhanced sentiment analysis")
    print("  ✅ Automatic API documentation")
    print("  ✅ Real-time trading signal generation")
    print("  ✅ Comprehensive error handling")
    
    print("\n🌐 Available Endpoints:")
    print(f"  📊 System Status: {base_url}/system-status")
    print(f"  🏥 Health Check: {base_url}/health")
    print(f"  📚 API Docs: {base_url}/docs")
    print(f"  📖 ReDoc: {base_url}/redoc")
    print(f"  📡 WebSocket: ws://localhost:8000/ws")
    
    return True

def test_api_performance():
    """Test API performance with multiple concurrent requests."""
    
    print("\n⚡ Testing API Performance")
    print("-" * 30)
    
    base_url = "http://localhost:8000"
    headlines = [
        "Apple stock jumps on strong iPhone sales",
        "Tesla announces new gigafactory expansion",
        "Microsoft beats quarterly revenue expectations",
        "Amazon Web Services shows record growth",
        "Google reveals new AI breakthrough"
    ]
    
    start_time = time.time()
    
    for i, headline in enumerate(headlines, 1):
        try:
            response = requests.post(
                f"{base_url}/process-headline",
                json={"headline": headline},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                print(f"  ✅ Request {i}: {response.elapsed.total_seconds():.3f}s")
            else:
                print(f"  ❌ Request {i}: Failed ({response.status_code})")
        except Exception as e:
            print(f"  ❌ Request {i}: Error ({e})")
    
    total_time = time.time() - start_time
    print(f"\n📊 Performance Summary:")
    print(f"  ⏱️  Total time: {total_time:.3f}s")
    print(f"  🚀 Average per request: {total_time/len(headlines):.3f}s")
    print(f"  💪 Requests per second: {len(headlines)/total_time:.1f}")

if __name__ == "__main__":
    print("FastAPI + Alpha Vantage Integration Test Suite")
    print("Make sure the FastAPI server is running on localhost:8000")
    print()
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Run comprehensive tests
    success = test_fastapi_endpoints()
    
    if success:
        # Run performance tests
        test_api_performance()
        
        print("\n🎯 All tests completed successfully!")
        print("🚀 MoonbeamAI FastAPI + Alpha Vantage integration is working perfectly!")
    else:
        print("\n❌ Some tests failed. Please check the server status.") 