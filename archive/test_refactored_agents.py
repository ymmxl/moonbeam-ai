#!/usr/bin/env python3
"""
Test script to demonstrate the refactored ticker extraction and sentiment aggregation functionality.
"""
import asyncio
import sys
import os

# Add agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from agents.ticker_mapper_agent import TickerMapperAgent
from agents.sentiment_aggregator_agent import SentimentAggregatorAgent
from agents.headline_classifier_agent import HeadlineClassifierAgent

async def test_individual_agents():
    """Test each agent individually."""
    print("=== Testing Individual Agents ===\n")
    
    # Initialize agents
    print("Initializing agents...")
    ticker_mapper = TickerMapperAgent(extraction_method="hybrid")
    sentiment_aggregator = SentimentAggregatorAgent(window_minutes=10)
    headline_classifier = HeadlineClassifierAgent()
    
    # Test headlines
    test_headlines = [
        "Apple reports record quarterly earnings, beating Wall Street expectations",
        "Tesla stock surges after strong delivery numbers for Q4",
        "Microsoft and Amazon announce strategic partnership",
        "I am going to buy 100 shares of cake tomorrow",  # Edge case
        "AAPL and MSFT stocks rise on positive market sentiment"
    ]
    
    print(f"\nTesting with {len(test_headlines)} headlines...\n")
    
    for i, headline in enumerate(test_headlines, 1):
        print(f"--- Test Case {i}: {headline} ---")
        
        # Step 1: Classify sentiment
        sentiment_result = await headline_classifier.process(headline)
        print(f"Sentiment: {sentiment_result}")
        
        # Step 2: Extract tickers
        tickers = await ticker_mapper.process(headline)
        print(f"Extracted Tickers: {tickers}")
        
        # Step 3: Aggregate sentiment (if tickers found)
        if tickers:
            timestamp = f"2025-05-26T12:{i:02d}:00Z"
            aggregated_result = await sentiment_aggregator.process((timestamp, sentiment_result, tickers))
            print(f"Aggregated Sentiment: {aggregated_result}")
        else:
            print("No aggregation (no tickers found)")
        
        print()

async def test_pipeline_integration():
    """Test the complete pipeline integration."""
    print("\n=== Testing Pipeline Integration ===\n")
    
    # Initialize agents
    ticker_mapper = TickerMapperAgent(extraction_method="hybrid")
    sentiment_aggregator = SentimentAggregatorAgent(window_minutes=5)
    headline_classifier = HeadlineClassifierAgent()
    
    # Simulate processing multiple headlines over time
    headlines_batch = [
        "Apple stock rises 5% after strong iPhone sales report",
        "Apple faces regulatory scrutiny in Europe",
        "Microsoft Azure cloud revenue grows 30% year-over-year", 
        "Tesla delivers record number of vehicles in Q4",
        "Apple announces new AI features for iPhone"
    ]
    
    print("Processing headlines in sequence to show aggregation...")
    
    for i, headline in enumerate(headlines_batch):
        print(f"\n--- Processing Headline {i+1}: {headline} ---")
        
        # Complete pipeline
        sentiment_data = await headline_classifier.process(headline)
        tickers = await ticker_mapper.process(headline)
        
        if tickers:
            timestamp = f"2025-05-26T12:{i+10:02d}:00Z"
            aggregated_data = await sentiment_aggregator.process((timestamp, sentiment_data, tickers))
            
            print(f"Tickers: {tickers}")
            print(f"Sentiment Score: {sentiment_data.get('sentiment_score', 'N/A')}")
            print(f"Aggregated Data: {aggregated_data}")
        else:
            print("No tickers extracted")
    
    # Show final state
    print(f"\n--- Final Aggregation State ---")
    print(f"All tracked tickers: {sentiment_aggregator.get_all_tickers()}")
    
    for ticker in sentiment_aggregator.get_all_tickers():
        history = sentiment_aggregator.get_ticker_history(ticker)
        print(f"{ticker} history: {len(history)} data points")

async def test_different_extraction_methods():
    """Test different ticker extraction methods."""
    print("\n=== Testing Different Extraction Methods ===\n")
    
    test_headline = "Apple and Microsoft stocks surge while Tesla faces challenges"
    
    methods = ["rule_based", "ml_model", "hybrid"]
    
    for method in methods:
        print(f"--- Testing {method} method ---")
        try:
            ticker_mapper = TickerMapperAgent(extraction_method=method)
            tickers = await ticker_mapper.process(test_headline)
            print(f"Extracted tickers: {tickers}")
        except Exception as e:
            print(f"Error with {method}: {e}")
        print()

async def main():
    """Run all tests."""
    print("Starting Refactored Agents Test Suite")
    print("=" * 50)
    
    try:
        await test_individual_agents()
        await test_pipeline_integration() 
        await test_different_extraction_methods()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 