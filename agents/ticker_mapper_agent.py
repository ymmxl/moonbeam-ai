import re
import csv
import os
from typing import Dict, List, Optional, Union
import aiohttp
import asyncio
from .base_agent import BaseAgent
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

class TickerMapperAgent(BaseAgent):
    """Agent that maps company names in headlines to ticker symbols using multiple extraction methods."""
    
    def __init__(self, ticker_file: Optional[str] = None, extraction_method: str = "ml_model"):
        super().__init__("TickerMapper")
        self.company_to_ticker = {}
        self.ticker_cache = {}
        self.extraction_method = extraction_method  # "rule_based", "ml_model", "hybrid"
        
        # Load company-to-ticker mapping from CSV if provided
        if ticker_file and os.path.exists(ticker_file):
            self._load_ticker_mapping(ticker_file)
        else:
            # Enhanced default mappings for common companies
            self.company_to_ticker = {
                "apple": "AAPL", "apple inc": "AAPL", "apple inc.": "AAPL",
                "microsoft": "MSFT", "microsoft corp": "MSFT", "microsoft corporation": "MSFT",
                "amazon": "AMZN", "amazon.com": "AMZN", "amazon inc": "AMZN",
                "google": "GOOGL", "alphabet": "GOOGL", "alphabet inc": "GOOGL",
                "facebook": "META", "meta": "META", "meta platforms": "META",
                "tesla": "TSLA", "tesla inc": "TSLA", "tesla motors": "TSLA",
                "netflix": "NFLX", "netflix inc": "NFLX",
                "nvidia": "NVDA", "nvidia corp": "NVDA", "nvidia corporation": "NVDA",
                "jpmorgan": "JPM", "jpmorgan chase": "JPM", "jp morgan": "JPM",
                "goldman sachs": "GS", "goldman": "GS",
                "bank of america": "BAC", "bofa": "BAC",
                "walmart": "WMT", "wal-mart": "WMT",
                "disney": "DIS", "walt disney": "DIS",
                "coca-cola": "KO", "coke": "KO", "coca cola": "KO",
                "intel": "INTC", "intel corp": "INTC",
                "amd": "AMD", "advanced micro devices": "AMD",
                "ibm": "IBM", "international business machines": "IBM",
                "berkshire hathaway": "BRK.A", "berkshire": "BRK.A",
                "johnson & johnson": "JNJ", "j&j": "JNJ", "johnson and johnson": "JNJ",
                "procter & gamble": "PG", "p&g": "PG", "procter and gamble": "PG",
                "visa": "V", "visa inc": "V",
                "mastercard": "MA", "mastercard inc": "MA",
                "home depot": "HD", "homedepot": "HD",
                "pfizer": "PFE", "pfizer inc": "PFE",
                "verizon": "VZ", "verizon communications": "VZ",
                "at&t": "T", "att": "T", "at and t": "T",
                "exxon mobil": "XOM", "exxon": "XOM", "exxonmobil": "XOM",
                "chevron": "CVX", "chevron corp": "CVX"
            }
        
        # Initialize ML model for ticker extraction if using ML methods
        if self.extraction_method in ["ml_model", "hybrid"]:
            self._initialize_ml_model()
    
    def _initialize_ml_model(self) -> None:
        """Initialize the ML model for ticker extraction."""
        try:
            self.ticker_tokenizer = AutoTokenizer.from_pretrained("Jean-Baptiste/roberta-ticker")
            self.ticker_model = AutoModelForTokenClassification.from_pretrained("Jean-Baptiste/roberta-ticker")
            self.ticker_nlp = pipeline('ner', model=self.ticker_model, tokenizer=self.ticker_tokenizer, aggregation_strategy="simple")
            self.logger.info("Initialized ML model for ticker extraction")
        except Exception as e:
            self.logger.error(f"Failed to initialize ML model: {e}")
            if self.extraction_method == "ml_model":
                self.extraction_method = "rule_based"
                self.logger.warning("Falling back to rule-based extraction")

    def _load_ticker_mapping(self, file_path: str) -> None:
        """Load company-to-ticker mapping from a CSV file."""
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 2:
                        company_name = row[0].lower()
                        ticker = row[1].upper()
                        self.company_to_ticker[company_name] = ticker
            
            self.logger.info(f"Loaded {len(self.company_to_ticker)} company-ticker mappings")
        except Exception as e:
            self.logger.error(f"Failed to load ticker mapping: {e}")
    
    def _extract_tickers_rule_based(self, news_text: str) -> List[str]:
        """
        Extract ticker symbols using rule-based approach.
        
        Args:
            news_text: The news text to extract tickers from
            
        Returns:
            List of ticker symbols found in the text
        """
        news_lower = news_text.lower()
        found_tickers = []
        
        # Check for each company name in our mapping
        for company, ticker in self.company_to_ticker.items():
            if company in news_lower and ticker not in found_tickers:
                found_tickers.append(ticker)
        
        # Also look for explicit ticker mentions (3-5 uppercase letters)
        ticker_pattern = r'\b[A-Z]{2,5}\b'
        potential_tickers = re.findall(ticker_pattern, news_text)
        
        for ticker in potential_tickers:
            # Filter out common false positives
            if ticker not in ['USA', 'CEO', 'CFO', 'IPO', 'SEC', 'FDA', 'API'] and ticker not in found_tickers:
                found_tickers.append(ticker)
        
        return found_tickers
    
    def _extract_tickers_ml_model(self, news_text: str) -> List[str]:
        """
        Extract ticker symbols using ML model (roberta-ticker).
        
        Args:
            news_text: The news text to extract tickers from
            
        Returns:
            List of ticker symbols found in the text
        """
        try:
            # Use the NLP pipeline to extract tickers
            entities = self.ticker_nlp(news_text)
            
            # Extract ticker symbols from the entities
            tickers = []
            for entity in entities:
                if entity['entity_group'] == 'TICKER':
                    ticker = entity['word'].strip().upper()
                    # Clean up subword tokens (remove ## prefixes)
                    ticker = ticker.replace('##', '')
                    if ticker and ticker not in tickers and len(ticker) >= 2:
                        tickers.append(ticker)
            
            return tickers
        except Exception as e:
            self.logger.error(f"Error extracting tickers with ML model: {e}")
            return []
    
    def _extract_tickers_hybrid(self, news_text: str) -> List[str]:
        """
        Extract ticker symbols using hybrid approach (rule-based + ML).
        
        Args:
            news_text: The news text to extract tickers from
            
        Returns:
            List of ticker symbols found in the text
        """
        # Get results from both methods
        rule_based_tickers = self._extract_tickers_rule_based(news_text)
        ml_tickers = self._extract_tickers_ml_model(news_text)
        
        # Combine and deduplicate
        all_tickers = list(set(rule_based_tickers + ml_tickers))
        
        # Sort by confidence (rule-based results first, then ML results)
        final_tickers = []
        for ticker in rule_based_tickers:
            if ticker not in final_tickers:
                final_tickers.append(ticker)
        
        for ticker in ml_tickers:
            if ticker not in final_tickers:
                final_tickers.append(ticker)
        
        return final_tickers

    async def _fetch_ticker_from_api(self, company_name: str) -> Optional[str]:
        """
        Fetch ticker symbol for a company using an API (mock implementation).
        In a real implementation, this would use Yahoo Finance API or similar.
        """
        # Mock API call - in a real implementation, this would be an actual API call
        await asyncio.sleep(0.1)  # Simulate API latency
        
        # Check if we have this company in our mapping
        return self.company_to_ticker.get(company_name.lower())
    
    async def extract_tickers_from_news(self, news_text: str) -> List[str]:
        """
        Extract ticker symbols from news text using the configured method.
        This is the main public method for ticker extraction.
        
        Args:
            news_text: The news text to extract tickers from
            
        Returns:
            List of ticker symbols found in the text
        """
        if self.extraction_method == "rule_based":
            return self._extract_tickers_rule_based(news_text)
        elif self.extraction_method == "ml_model":
            return self._extract_tickers_ml_model(news_text)
        elif self.extraction_method == "hybrid":
            return self._extract_tickers_hybrid(news_text)
        else:
            self.logger.warning(f"Unknown extraction method: {self.extraction_method}")
            return self._extract_tickers_rule_based(news_text)

    async def process(self, input_data: Union[str, Dict[str, str]]) -> List[str]:
        """
        Extract ticker symbols from a headline or news text.
        
        Args:
            input_data: Either a string (headline/news text) or dict with 'news' key
            
        Returns:
            A list of ticker symbols mentioned in the text
        """
        # Handle different input formats
        if isinstance(input_data, dict):
            if "news" in input_data:
                news_text = input_data["news"]
            elif "headline" in input_data:
                news_text = input_data["headline"]
            else:
                self.logger.error("Invalid input format: expected 'news' or 'headline' key")
                return []
        else:
            news_text = str(input_data)
        
        # Extract tickers using the configured method
        found_tickers = await self.extract_tickers_from_news(news_text)
        
        # If no tickers found using primary method, try to extract potential company names
        if not found_tickers:
            # Extract potential company names (capitalized words)
            potential_companies = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', news_text)
            
            for company in potential_companies:
                if company.lower() not in self.ticker_cache:
                    ticker = await self._fetch_ticker_from_api(company)
                    if ticker:
                        self.ticker_cache[company.lower()] = ticker
                        found_tickers.append(ticker)
                else:
                    found_tickers.append(self.ticker_cache[company.lower()])
        
        # Remove duplicates while preserving order
        unique_tickers = []
        for ticker in found_tickers:
            if ticker not in unique_tickers:
                unique_tickers.append(ticker)
        
        return unique_tickers
    
if __name__ == "__main__":
    import asyncio
    c = TickerMapperAgent()
    r=asyncio.run(c.process("the SEC bans acquiring of the AAVE token with effective date of 2025-05-28"))
    print(r)