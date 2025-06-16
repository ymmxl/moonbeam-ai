#!/usr/bin/env python3
"""
Test API endpoints
"""

import requests
import json
import time

def test_endpoints():
    print("🚀 Testing API Endpoints")
    print("=" * 50)
    
    # Wait a moment for server to fully start
    time.sleep(3)
    
    try:
        # Test health endpoint
        print("\n📊 Testing health endpoint...")
        health_response = requests.get('http://localhost:8000/health')
        print(f'Health Status: {health_response.status_code}')
        print(f'Health Response: {health_response.json()}')
        
        # Test latest-news endpoint
        print("\n📰 Testing latest-news endpoint...")
        news_response = requests.get('http://localhost:8000/latest-news')
        print(f'News Status: {news_response.status_code}')
        if news_response.status_code == 200:
            news_data = news_response.json()
            print(f'News Response: Found {news_data.get("count", 0)} articles')
            if news_data.get("articles"):
                first_article = news_data["articles"][0]
                print(f'First article: {first_article.get("headline", "No headline")[:60]}...')
        else:
            print(f'News Error: {news_response.text}')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    test_endpoints() 