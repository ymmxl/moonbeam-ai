import os
import logging
import uvicorn
from api import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")

if __name__ == "__main__":
    # Create log directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    logger.info("🚀 Starting MoonbeamAI Financial News Sentiment Trading System with FastAPI")
    logger.info("🌟 Powered by Alpha Vantage real-time financial news")
    
    # Run the FastAPI app with uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        reload=False  # Set to True for development
    )
    




    # todo:
       # maybe change it to be a web app that gives weekly overview of the ticker based on a week of news data sentiment
    # 1. add a way to add a new ticker to the system
    # 2. add a way to remove a ticker from the system
    # 3. add a way to update the sentiment of a ticker
    # 4. add a way to get the sentiment of a ticker
    # 5. add a way to get the sentiment of all tickers
    # 6. add a way to get the sentiment of a ticker over a period of time
    # 7. add a way to get the sentiment of all tickers over a period of time
 