import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit

from system_coordinator import SystemCoordinator
from headline_simulator import HeadlineSimulator
from alpha_vantage_news_fetcher import AlphaVantageNewsFetcher
from google_news_fetcher import GoogleNewsFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FlaskApp")

# Configuration
ALPHA_VANTAGE_API_KEY = "42UELCP2HWG56JHF"
USE_ALPHA_VANTAGE_NEWS = False  # Set to False to use Google News instead
USE_GOOGLE_NEWS = True  # Set to False to use simulator instead
USE_ALPHA_VANTAGE_SENTIMENT = True  # Set to False to use basic sentiment analysis
NEWS_FETCH_INTERVAL = 600  # 10 minutes in seconds

# Helper function to run async functions in Flask
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(coro)
    loop.close()
    return result

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'financial-news-sentiment-system'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize system coordinator with Alpha Vantage support
coordinator = SystemCoordinator(
    alpha_vantage_api_key=ALPHA_VANTAGE_API_KEY,
    use_alpha_vantage_sentiment=USE_ALPHA_VANTAGE_SENTIMENT
)

# Initialize news sources
simulator = HeadlineSimulator()
if USE_ALPHA_VANTAGE_NEWS and ALPHA_VANTAGE_API_KEY:
    news_fetcher = AlphaVantageNewsFetcher(ALPHA_VANTAGE_API_KEY)
    logger.info("Using Alpha Vantage real news data")
elif USE_GOOGLE_NEWS:
    news_fetcher = GoogleNewsFetcher(lang='en', region='US')
    logger.info("Using Google News real news data")
else:
    news_fetcher = simulator
    logger.info("Using simulated news data")

# Background task to run the news fetcher
def run_news_stream():
    async def process_news():
        if USE_ALPHA_VANTAGE_NEWS and ALPHA_VANTAGE_API_KEY:
            await news_fetcher.start_stream(coordinator.process_headline, interval_seconds=NEWS_FETCH_INTERVAL)
        elif USE_GOOGLE_NEWS:
            await news_fetcher.start_stream(coordinator.process_headline, interval_seconds=NEWS_FETCH_INTERVAL)
        else:
            await simulator.start_stream(coordinator.process_headline, interval_seconds=10)
    
    # Run in a separate thread
    import threading
    thread = threading.Thread(target=lambda: run_async(process_news()))
    thread.daemon = True
    thread.start()

# Signal listener for WebSocket broadcasts
async def signal_listener(signals):
    # Convert signals to JSON-serializable format if needed
    serializable_signals = json.loads(json.dumps(signals))
    socketio.emit('signals', {'type': 'signals', 'data': serializable_signals})

# Register the signal listener
coordinator.add_signal_listener(signal_listener)

# Start the news stream
with app.app_context():
    run_news_stream()

# Routes
@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/process-headline', methods=['POST'])
def process_headline():
    """Process a single headline and return the results."""
    data = request.json
    headline = data.get('headline', '')
    
    if not headline:
        return jsonify({'error': 'No headline provided'}), 400
    
    signals = run_async(coordinator.process_headline(headline))
    
    return jsonify({
        'headline': headline,
        'signals': signals
    })

@app.route('/latest-signals')
def get_latest_signals():
    """Get the latest trading signals."""
    signals = run_async(coordinator.get_latest_signals())
    return jsonify(signals)

@app.route('/signal-history')
def get_signal_history():
    """Get the history of trading signals."""
    history = run_async(coordinator.get_signal_history())
    return jsonify(history)

@app.route('/system-status')
def get_system_status():
    """Get system status and configuration."""
    status = run_async(coordinator.get_system_status())
    
    # Add news fetcher information
    if USE_ALPHA_VANTAGE_NEWS and hasattr(news_fetcher, 'get_api_usage_info'):
        status['news_fetcher'] = {
            'type': 'Alpha Vantage',
            'api_usage': news_fetcher.get_api_usage_info(),
            'fetch_interval_seconds': NEWS_FETCH_INTERVAL
        }
    elif USE_GOOGLE_NEWS and hasattr(news_fetcher, 'get_api_usage_info'):
        status['news_fetcher'] = {
            'type': 'Google News',
            'api_usage': news_fetcher.get_api_usage_info(),
            'fetch_interval_seconds': NEWS_FETCH_INTERVAL
        }
    else:
        status['news_fetcher'] = {
            'type': 'Simulator',
            'interval_seconds': 10
        }
    
    return jsonify(status)

@app.route('/fetch-news', methods=['POST'])
def manual_fetch_news():
    """Manually trigger a news fetch (for testing)."""
    try:
        if (USE_ALPHA_VANTAGE_NEWS or USE_GOOGLE_NEWS) and hasattr(news_fetcher, 'fetch_latest_news'):
            if USE_ALPHA_VANTAGE_NEWS:
                # Alpha Vantage returns headlines directly
                headlines = run_async(news_fetcher.fetch_latest_news())
                # Process each headline
                results = []
                for headline in headlines[:5]:  # Limit to 5 headlines for manual testing
                    signals = run_async(coordinator.process_headline(headline))
                    results.append({
                        'headline': headline,
                        'signals': signals
                    })
                
                return jsonify({
                    'success': True,
                    'headlines_fetched': len(headlines),
                    'results': results
                })
            elif USE_GOOGLE_NEWS:
                # Google News returns full articles
                articles = run_async(news_fetcher.fetch_latest_news())
                # Process each article's headline
                results = []
                for article in articles[:5]:  # Limit to 5 articles for manual testing
                    headline = article.get('headline', '')
                    if headline:
                        signals = run_async(coordinator.process_headline(headline))
                        results.append({
                            'headline': headline,
                            'description': article.get('description', ''),
                            'url': article.get('url', ''),
                            'source': article.get('source', {}),
                            'signals': signals
                        })
                
                return jsonify({
                    'success': True,
                    'articles_fetched': len(articles),
                    'results': results
                })
        else:
            return jsonify({'error': 'News fetcher not available'}), 400
            
    except Exception as e:
        logger.error(f"Error in manual news fetch: {e}")
        return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info("Client connected")
    # Send current system status to newly connected client
    status = run_async(coordinator.get_system_status())
    emit('system_status', status)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info("Client disconnected")

@socketio.on('request_status')
def handle_status_request():
    """Handle status request from client."""
    status = run_async(coordinator.get_system_status())
    emit('system_status', status)

if __name__ == '__main__':
    # Create log directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    logger.info(f"Starting moonbeamAI with news integration...")
    logger.info(f"Alpha Vantage News: {'Enabled' if USE_ALPHA_VANTAGE_NEWS else 'Disabled'}")
    logger.info(f"Google News: {'Enabled' if USE_GOOGLE_NEWS else 'Disabled'}")
    logger.info(f"Alpha Vantage Sentiment: {'Enabled' if USE_ALPHA_VANTAGE_SENTIMENT else 'Disabled'}")
    logger.info(f"News fetch interval: {NEWS_FETCH_INTERVAL} seconds")

    # Run the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)