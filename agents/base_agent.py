import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
import json
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.output_queue = asyncio.Queue()
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process the input data and return the result."""
        pass
    
    async def log_output(self, input_data: Any, output_data: Any) -> None:
        """Log the input and output data."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "agent": self.name,
            "input": input_data,
            "output": output_data
        }
        
        # Log to console
        self.logger.info(f"Agent: {self.name} - Input: {input_data} - Output: {output_data}")
        
        # Log to JSON file
        try:
            with open(f"logs/{self.name}_logs.json", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write to log file: {e}")
        
        # Put the output in the queue for the next agent
        await self.output_queue.put((timestamp, output_data))
    
    async def run(self, input_data: Any) -> Any:
        """Run the agent on the input data and log the result."""
        result = await self.process(input_data)
        await self.log_output(input_data, result)
        return result