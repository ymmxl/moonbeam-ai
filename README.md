# Moonbeam AI

A sophisticated financial news analysis system that combines sentiment analysis and ticker extraction capabilities.

## Features

- **Financial News Fetching**: Real-time financial news retrieval using Google News API
- **Sentiment Analysis**: Advanced sentiment classification of financial headlines
- **Ticker Extraction**: Intelligent extraction of stock tickers from news headlines
- **Multi-Model Architecture**: Combines transformer models for optimal performance

## Components

### Headline Classifier Agent
- Sentiment analysis using `mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis`
- Ticker extraction using NER models with regex fallback
- Configurable sentiment scoring and ticker validation

### Google News Fetcher
- Real-time financial news retrieval
- Batch processing with pagination
- Smart filtering for financial relevance
- Duplicate detection and removal

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/moonbeam-ai.git
cd moonbeam-ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```python
from agents.headline_classifier_agent import HeadlineClassifierAgent
from google_news_fetcher import GoogleNewsFetcher

# Initialize components
classifier = HeadlineClassifierAgent()
fetcher = GoogleNewsFetcher()

# Fetch and process news
headlines = await fetcher.fetch_headlines_batch(batch_size=10)
for headline in headlines:
    result = await classifier.process(headline)
    print(f"Headline: {headline}")
    print(f"Sentiment: {result['label']}")
    print(f"Tickers: {result['tickers']}")
```

## Requirements

- Python 3.8+
- PyTorch
- Transformers
- GoogleNews API

## License

MIT License
