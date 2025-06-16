# 🌙 MoonbeamAI: Financial News Sentiment Trading System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MoonbeamAI is a sophisticated financial news sentiment analysis system that generates real-time trading signals by processing financial headlines through a multi-agent AI pipeline. The system combines advanced NLP sentiment analysis with ticker extraction and temporal aggregation to produce actionable trading insights.

[70% Vibe Coded with Cursor, 30% Bug Finding]

## 🎯 Strategy & Vision

### Trading Strategy
The core hypothesis behind MoonbeamAI is that **aggregate sentiment trends from financial news can predict short-term price movements**. The system:

1. **Captures Market Sentiment**: Processes real-time financial news to extract sentiment signals
2. **Temporal Aggregation**: Uses an 8-hour rolling window to smooth out noise and identify trends
3. **Multi-Signal Analysis**: Combines sentiment strength, confidence scores, and headline frequency
4. **Risk Management**: Applies configurable thresholds to reduce false signals

### Investment Philosophy
- **Data-Driven Decisions**: Every signal is backed by quantitative sentiment analysis
- **Trend Following**: Focus on momentum rather than contrarian plays
- **Risk-Aware**: Conservative thresholds prioritize signal quality over quantity
- **Scalable**: Architecture supports processing thousands of news articles daily

## 🏗️ Architecture

MoonbeamAI uses a **multi-agent pipeline architecture** where specialized AI agents handle different aspects of the analysis:

```
📰 News Sources → 🤖 Agent Pipeline → 📊 Trading Signals
```

### Core Components

#### 1. **News Ingestion Layer**
- **TickerTick Integration**: Real-time financial news with pre-extracted tickers (powered by [TickerTick API](https://github.com/hczhu/TickerTick-API))
- **Google News Fallback**: Alternative news source for broader coverage
- **Headline Simulator**: Synthetic data for testing and development

#### 2. **AI Agent Pipeline**
- **Headline Classifier Agent**: Sentiment analysis using NER and transformer models
- **Sentiment Aggregator Agent**: Temporal aggregation with confidence weighting
- **Signal Decision Agent**: Converts sentiment trends into trading signals

#### 3. **System Coordinator**
- Orchestrates data flow between agents
- Manages system state and configuration
- Handles real-time broadcasting to clients

#### 4. **API Layer**
- **FastAPI Backend**: High-performance async API with WebSocket support
- **Flask Frontend**: Alternative web interface for legacy compatibility
- **Real-time Updates**: WebSocket connections for live signal streaming

## 🚀 Features

### Core Functionality
- ✅ **Real-time News Processing**: Live financial news analysis from multiple sources
- ✅ **Sentiment Analysis**: Advanced NLP models for financial sentiment classification
- ✅ **Ticker Extraction**: Intelligent mapping of news to stock symbols
- ✅ **Trading Signals**: LONG/SHORT/FLAT recommendations with confidence scores
- ✅ **Temporal Aggregation**: 8-hour rolling windows for trend analysis
- ✅ **WebSocket Streaming**: Real-time signal delivery to clients

### Advanced Features
- 🔄 **Multi-Model Support**: Configurable sentiment analysis backends
- 📊 **Historical Analysis**: Signal history and performance tracking
- 🎛️ **Configurable Thresholds**: Customizable risk parameters
- 🔍 **Ticker-Specific Analysis**: Per-stock sentiment and signal tracking
- 📱 **Web Interface**: Clean, modern UI for monitoring and control

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip or uv package manager

### Quick Start

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/moonbeamAI.git
cd moonbeamAI
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
# OR using uv
uv sync
```

4. **Run the application**:
```bash
# FastAPI (recommended)
python api.py
# OR
uvicorn api:app --reload

# Flask (alternative)
python app.py
```

5. **Access the interface**:
- FastAPI: http://localhost:8000
- Flask: http://localhost:5000

## 💻 Usage

### API Endpoints

#### Core Endpoints
```bash
# Process a single headline
POST /process-headline
{
  "headline": "Apple reports record Q4 earnings, beats expectations"
}

# Get latest trading signals
GET /latest-signals

# Get signals for specific ticker
GET /signals-by-ticker

# Get signal history
GET /signal-history

# Manual news fetch
POST /fetch-news
```

#### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'signals') {
        console.log('New signals:', data.data);
    }
};
```

### Python Integration

```python
import asyncio
from system_coordinator import SystemCoordinator

# Initialize the system
coordinator = SystemCoordinator()

# Process a headline
async def analyze_news():
    signals = await coordinator.process_headline(
        "Tesla stock surges on strong delivery numbers"
    )
    print(f"Generated signals: {signals}")

# Run the analysis
asyncio.run(analyze_news())
```

### Configuration

Create a `.env` file for configuration:
```bash
# News Source Configuration
USE_TICKERTICK_NEWS=true
NEWS_FETCH_INTERVAL=180

# Sentiment Analysis
USE_ALPHA_VANTAGE_SENTIMENT=false

# API Keys (optional)
ALPHA_VANTAGE_API_KEY=your_key_here
```

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_api_endpoints.py
python -m pytest tests/test_fastapi_integration.py
```

## 📊 Signal Interpretation

### Signal Types
- **LONG**: Positive sentiment trend, consider buying
- **SHORT**: Negative sentiment trend, consider selling  
- **FLAT**: Neutral or insufficient data, no action recommended

### Confidence Levels
- **High (0.8-1.0)**: Strong signal backed by multiple high-confidence headlines
- **Medium (0.6-0.8)**: Moderate signal with some uncertainty
- **Low (0.0-0.6)**: Weak signal, use with caution

### Example Signal Output
```json
{
  "AAPL": {
    "signal": "LONG",
    "confidence": 0.85,
    "sentiment_score": 0.73,
    "headline_count": 12,
    "last_updated": "2024-01-15T10:30:00Z"
  }
}
```

## 🔧 Configuration

### Agent Configuration
The system supports various configuration options:

```python
# Sentiment Aggregator
window_minutes = 8 * 60  # 8-hour rolling window
confidence_threshold = 0.1

# Signal Decision
positive_threshold = 0.7  # Threshold for LONG signals
negative_threshold = -0.7  # Threshold for SHORT signals
min_headlines = 2  # Minimum headlines required
```

### News Sources
- **TickerTick**: Real-time financial news with ticker extraction ([TickerTick API](https://github.com/hczhu/TickerTick-API))
- **Google News**: Broader news coverage with custom ticker mapping
- **Simulator**: Synthetic headlines for testing

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run linting
flake8 .
black .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**Important**: This software is for educational and research purposes only. MoonbeamAI is not financial advice and should not be used as the sole basis for investment decisions. Always:

- Conduct your own research
- Consult with financial advisors
- Understand the risks involved in trading
- Never invest more than you can afford to lose

The authors and contributors are not responsible for any financial losses incurred through the use of this software.

## 📋 TODO

- [ ] **Deploy to HuggingFace Spaces**: Set up live demo on HuggingFace Spaces for easy testing
- [ ] **Performance benchmarking**: Add backtesting framework for signal validation
- [ ] **Enhanced visualization**: Real-time charts and signal performance metrics

## 🔗 Links

- **Documentation**: [Coming Soon]
- **Issues**: [GitHub Issues](https://github.com/yourusername/moonbeamAI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/moonbeamAI/discussions)

## 🙏 Acknowledgments

- **TickerTick API**: Financial news data and ticker information provided by [TickerTick API](https://github.com/hczhu/TickerTick-API) - A powerful stock news API that covers all companies listed in US stock markets with a sophisticated query language
- Sentiment analysis models from Hugging Face Transformers
- Built with FastAPI, Flask, and modern Python tooling

---

*Built with ❤️ for the financial technology community*
