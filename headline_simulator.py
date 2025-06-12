import asyncio
import random
from datetime import datetime
from typing import List, Callable, Awaitable

class HeadlineSimulator:
    """
    Simulates a stream of financial headlines for testing.
    """
    
    def __init__(self):
        self.companies = [
            "Apple", "Microsoft", "Amazon", "Google", "Facebook", "Tesla", 
            "Netflix", "Nvidia", "JPMorgan", "Goldman Sachs", "Bank of America",
            "Walmart", "Disney", "Coca-Cola", "Intel", "AMD", "IBM"
        ]
        
        self.positive_templates = [
            "{company} reports record earnings in Q{quarter}",
            "{company} stock surges after beating analyst expectations",
            "{company} announces new product line, shares jump",
            "{company} expands into {market}, investors optimistic",
            "{company} raises guidance for fiscal year",
            "{company} CEO announces ambitious growth plans",
            "Analysts upgrade {company} to 'buy' rating",
            "{company} partners with {partner} in strategic alliance"
        ]
        
        self.negative_templates = [
            "{company} misses earnings expectations in Q{quarter}",
            "{company} stock plunges on disappointing results",
            "{company} announces layoffs amid restructuring",
            "{company} faces regulatory scrutiny in {market}",
            "{company} lowers guidance for fiscal year",
            "{company} CEO steps down amid controversy",
            "Analysts downgrade {company} to 'sell' rating",
            "{company} loses market share to {partner}"
        ]
        
        self.neutral_templates = [
            "{company} reports Q{quarter} earnings in line with expectations",
            "{company} maintains current outlook for fiscal year",
            "{company} announces management changes",
            "{company} to present at upcoming investor conference",
            "{company} releases statement on {market} conditions",
            "{company} neither confirms nor denies {partner} acquisition rumors",
            "Analysts maintain 'hold' rating on {company}",
            "{company} completes previously announced share repurchase program"
        ]
    
    def _generate_headline(self) -> str:
        """Generate a random financial headline."""
        company = random.choice(self.companies)
        partner = random.choice([c for c in self.companies if c != company])
        quarter = random.choice(["1", "2", "3", "4"])
        market = random.choice(["US", "European", "Asian", "global", "emerging"])
        
        # Choose sentiment bias (slightly more positive than negative)
        sentiment_roll = random.random()
        if sentiment_roll > 0.6:  # 40% positive
            template = random.choice(self.positive_templates)
        elif sentiment_roll > 0.3:  # 30% neutral
            template = random.choice(self.neutral_templates)
        else:  # 30% negative
            template = random.choice(self.negative_templates)
        
        # Fill in the template
        headline = template.format(
            company=company,
            partner=partner,
            quarter=quarter,
            market=market
        )
        
        return headline
    
    async def start_stream(self, callback: Callable[[str], Awaitable[None]], interval_seconds: float = 5.0):
        """
        Start streaming headlines at the specified interval.
        
        Args:
            callback: Async function to call with each headline
            interval_seconds: Interval between headlines in seconds
        """
        while True:
            headline = self._generate_headline()
            await callback(headline)
            await asyncio.sleep(interval_seconds)