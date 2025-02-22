from datetime import datetime
from typing import List
import asyncio
from loguru import logger
from .mock_data import get_mock_historical_data
from ..domain.models import StockData

class MockZerodhaClient:
    def __init__(self):
        pass
    
    async def fetch_historical_data(self, symbol: str, from_date: datetime, to_date: datetime) -> List[StockData]:
        try:
            logger.info(f"Fetching mock data for {symbol} from {from_date} to {to_date}")
            
            # Get mock data
            response = get_mock_historical_data(symbol, from_date, to_date)
            data = response["data"]["candles"]
            
            # Simulate API delay
            await asyncio.sleep(0.5)
            
            return [
                StockData(
                    symbol=symbol,
                    timestamp=datetime.fromisoformat(record[0].replace("+0530", "")),
                    open=float(record[1]),
                    high=float(record[2]),
                    low=float(record[3]),
                    close=float(record[4]),
                    volume=int(record[5])
                ) for record in data
            ]
            
        except Exception as e:
            logger.error(f"Error generating mock data: {str(e)}")
            raise 