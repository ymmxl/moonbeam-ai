import asyncio
import logging
from typing import Dict, List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from system_coordinator import SystemCoordinator
from headline_simulator import HeadlineSimulator
from tickertick_news_fetcher import TickerTickNewsFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FastAPI")

# Configuration
USE_TICKERTICK_NEWS = True  # Set to False to use simulator instead
USE_ALPHA_VANTAGE_SENTIMENT = False  # We'll use sentiment_aggregator_agent instead
NEWS_FETCH_INTERVAL = 180  # 3 minutes in seconds (respects TickerTick's 10 requests/minute limit)

# Initialize FastAPI app
app = FastAPI(
    title="MoonbeamAI: Financial News Sentiment Trading System",
    description="Real-time financial news sentiment analysis with TickerTick integration",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize system coordinator without Alpha Vantage sentiment (use our own agents)
coordinator = SystemCoordinator(
    alpha_vantage_api_key=None,
    use_alpha_vantage_sentiment=USE_ALPHA_VANTAGE_SENTIMENT
)

# Initialize news sources
simulator = HeadlineSimulator()
if USE_TICKERTICK_NEWS:
    news_fetcher = TickerTickNewsFetcher()
    logger.info("Using TickerTick real news data")
else:
    news_fetcher = simulator
    logger.info("Using simulated news data")

# Store latest news articles with full data
latest_news_articles = []

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        if self.active_connections:
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to WebSocket client: {e}")

manager = ConnectionManager()

# Signal listener for WebSocket broadcasts
async def signal_listener(signals):
    await manager.broadcast({
        "type": "signals",
        "data": signals
    })

# News listener for WebSocket broadcasts
async def news_listener(news_articles):
    global latest_news_articles
    latest_news_articles = news_articles[-10:]  # Keep last 10 articles
    await manager.broadcast({
        "type": "news",
        "data": latest_news_articles
    })

# Register the signal listener
coordinator.add_signal_listener(signal_listener)

# Enhanced news processing function
async def process_news_articles(news_articles: List[Dict[str, Any]]):
    """Process news articles and extract trading signals."""
    try:
        # Broadcast news to WebSocket clients
        await news_listener(news_articles)
        
        # Process each article using the enhanced method that utilizes existing tickers
        for article in news_articles:
            headline = article.get('headline', '')
            if headline:
                try:
                    # Use the enhanced method that handles pre-tickered articles
                    signals = await coordinator.process_news_article(article)
                    if signals:
                        logger.info(f"Generated signals for article: {headline[:50]}...")
                except Exception as e:
                    logger.warning(f"Error processing article '{headline}': {e}")
                    
        logger.info(f"Processed {len(news_articles)} news articles")
        
    except Exception as e:
        logger.error(f"Error processing news articles: {e}")

# Background task to run the news fetcher
async def start_news_stream():
    """Start the news stream in the background."""
    try:
        if USE_TICKERTICK_NEWS:
            logger.info(f"Starting TickerTick stream with {NEWS_FETCH_INTERVAL}s intervals")
            
            # TickerTick callback handles list of news articles
            async def tickertick_callback(news_articles):
                await process_news_articles(news_articles)
            
            # Start the news stream - this will call tickertick_callback with news articles
            # The stream will use the default 16-hour lookback period
            await news_fetcher.start_stream(tickertick_callback)
        else:
            logger.info("Starting headline simulator with 10s intervals")
            await simulator.start_stream(coordinator.process_headline, interval_seconds=10)
    except Exception as e:
        logger.error(f"Error in news stream: {e}")

# Pydantic models
class HeadlineInput(BaseModel):
    headline: str

class SystemStatusResponse(BaseModel):
    status: str
    configuration: Dict[str, Any]
    total_headlines_processed: int
    latest_signals_count: int
    sentiment_agent: str
    news_fetcher: Dict[str, Any]

class NewsArticle(BaseModel):
    headline: str
    description: str
    content: str
    url: str
    image: str
    published_at: str
    source: Dict[str, str]

# API routes
@app.get("/")
async def root(request: Request):
    """Render the main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process-headline")
async def process_headline(input_data: HeadlineInput):
    """Process a single headline and return the results."""
    try:
        signals = await coordinator.process_headline(input_data.headline)
        return {
            "headline": input_data.headline,
            "signals": signals,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error processing headline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest-signals")
async def get_latest_signals():
    """Get the latest trading signals."""
    try:
        return await coordinator.get_latest_signals()
    except Exception as e:
        logger.error(f"Error getting latest signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signals-by-ticker")
async def get_signals_by_ticker():
    """Get the current aggregated signals organized by ticker."""
    try:
        return await coordinator.get_signals_by_ticker()
    except Exception as e:
        logger.error(f"Error getting signals by ticker: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signal-history")
async def get_signal_history():
    """Get the history of trading signals."""
    try:
        return await coordinator.get_signal_history()
    except Exception as e:
        logger.error(f"Error getting signal history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest-news")
async def get_latest_news(lookback_hours: int = 16):
    """Get the latest news articles with snippets."""
    try:
        if USE_TICKERTICK_NEWS and hasattr(news_fetcher, 'fetch_latest_news'):
            news_articles = await news_fetcher.fetch_latest_news(lookback_hours=lookback_hours)
            return {
                "success": True,
                "articles": news_articles,
                "count": len(news_articles),
                "lookback_hours": lookback_hours
            }
        else:
            # Fallback to simulator
            headlines = await simulator.generate_headlines(5)
            articles = []
            for headline in headlines:
                articles.append({
                    "headline": headline,
                    "description": "Simulated news description for testing purposes.",
                    "content": f"This is simulated content for the headline: {headline}",
                    "url": "https://example.com",
                    "image": "",
                    "published_at": "2025-01-06T00:00:00Z",
                    "source": {"name": "Simulator", "url": "https://example.com"}
                })
            return {
                "success": True,
                "articles": articles,
                "count": len(articles)
            }
    except Exception as e:
        logger.error(f"Error getting latest news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system-status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get system status and configuration."""
    try:
        status = await coordinator.get_system_status()
        
        # Add news fetcher information
        if USE_TICKERTICK_NEWS and hasattr(news_fetcher, 'get_api_usage_info'):
            status['news_fetcher'] = {
                'type': 'TickerTick',
                'api_usage': news_fetcher.get_api_usage_info(),
                'fetch_interval_seconds': NEWS_FETCH_INTERVAL
            }
        else:
            status['news_fetcher'] = {
                'type': 'Simulator',
                'interval_seconds': 10
            }
        
        return status
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch-news")
async def manual_fetch_news(lookback_hours: int = 16):
    """Manually trigger a news fetch (for testing)."""
    try:
        if USE_TICKERTICK_NEWS and hasattr(news_fetcher, 'fetch_latest_news'):
            # Fetch full news articles
            news_articles = await news_fetcher.fetch_latest_news(lookback_hours=lookback_hours)
            
            # Process articles using the enhanced method that utilizes existing tickers
            results = []
            for article in news_articles[:5]:  # Limit to 5 articles for manual testing
                headline = article.get('headline', '')
                if headline:
                    try:
                        # Use the enhanced method that handles pre-tickered articles
                        signals = await coordinator.process_news_article(article)
                        results.append({
                            'headline': headline,
                            'description': article.get('description', ''),
                            'url': article.get('url', ''),
                            'source': article.get('source', {}),
                            'published_at': article.get('published_at', ''),
                            'tickers': article.get('tickers', []),
                            'signals': signals
                        })
                    except Exception as e:
                        logger.warning(f"Error processing article '{headline}': {e}")
                        results.append({
                            'headline': headline,
                            'description': article.get('description', ''),
                            'tickers': article.get('tickers', []),
                            'error': str(e)
                        })
            
            return {
                'success': True,
                'articles_fetched': len(news_articles),
                'lookback_hours': lookback_hours,
                'results': results
            }
        else:
            raise HTTPException(status_code=400, detail="TickerTick news fetcher not available")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual news fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-01-06T00:00:00Z",
        "version": "2.0.0",
        "ticker_tick_enabled": USE_TICKERTICK_NEWS,
        "sentiment_aggregator": "enabled"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        # Send initial system status
        status = await coordinator.get_system_status()
        await websocket.send_json({
            "type": "system_status",
            "data": status
        })
        
        # Send latest news if available
        if latest_news_articles:
            await websocket.send_json({
                "type": "news",
                "data": latest_news_articles
            })
        
        # Keep the connection alive
        while True:
            # Wait for messages from client (optional)
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle client messages
                if message == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message == "status":
                    status = await coordinator.get_system_status()
                    await websocket.send_json({
                        "type": "system_status", 
                        "data": status
                    })
                elif message == "news":
                    # Send latest news
                    news_data = await get_latest_news()
                    await websocket.send_json({
                        "type": "news",
                        "data": news_data.get("articles", [])
                    })
                    
            except asyncio.TimeoutError:
                # Send periodic heartbeat
                await websocket.send_json({"type": "heartbeat", "timestamp": "2025-01-06T00:00:00Z"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info(f"🚀 Starting MoonbeamAI with TickerTick integration...")
    logger.info(f"📰 TickerTick: {'Enabled' if USE_TICKERTICK_NEWS else 'Disabled'}")
    logger.info(f"💭 Sentiment Aggregator: Enabled")
    logger.info(f"⏱️  News fetch interval: {NEWS_FETCH_INTERVAL} seconds")
    
    # Start the news stream in the background
    asyncio.create_task(start_news_stream())
    
    logger.info("✅ MoonbeamAI FastAPI application started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    logger.info("🛑 Shutting down MoonbeamAI...")
    
    # Close all WebSocket connections
    for connection in manager.active_connections:
        try:
            await connection.close()
        except Exception as e:
            logger.warning(f"Error closing WebSocket connection: {e}")
    
    logger.info("✅ MoonbeamAI shutdown complete")

# Error handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )