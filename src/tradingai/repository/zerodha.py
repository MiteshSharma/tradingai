from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
from loguru import logger
from kiteconnect import KiteConnect
from ..domain.models import StockData
from ..config.settings import settings
from ..service.instrument_service import InstrumentService
from dataclasses import dataclass

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 60  # Zerodha's rate limit
CHUNK_SIZE_DAYS = 365  # Process 1 year at a time

@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
def call_api():
    return True

@dataclass
class HistoricalData:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class ZerodhaClient:
    def __init__(self, instrument_service: InstrumentService):
        self.base_url = "https://api.kite.trade"
        self.api_key = settings.ZERODHA_API_KEY
        self.instrument_service = instrument_service
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    @sleep_and_retry
    @limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
    async def fetch_historical_data(
        self, 
        symbol: str, 
        from_date: datetime,
        to_date: datetime,
        interval: str = "day"
    ) -> List[HistoricalData]:
        """
        Fetch historical OHLCV data from Zerodha
        Args:
            symbol: Trading symbol
            from_date: Start date
            to_date: End date
            interval: Candle interval (minute, day, etc.)
        Returns:
            List of HistoricalData objects
        """
        try:
            # Get instrument token
            instrument_token = await self.instrument_service.get_instrument_token(symbol)
            if not instrument_token:
                raise ValueError(f"Instrument token not found for symbol: {symbol}")

            # Format dates
            from_str = from_date.strftime("%Y-%m-%d %H:%M:%S")
            to_str = to_date.strftime("%Y-%m-%d %H:%M:%S")
            
            # Prepare request
            url = f"{self.base_url}/instruments/historical/{instrument_token}/{interval}"
            params = {
                "from": from_str,
                "to": to_str,
                "continuous": 0  # Changed from 1 to 0 for equity stocks
            }
            headers = {
                "X-Kite-Version": "3",
                "Authorization": f"token {self.api_key}:{settings.ZERODHA_ACCESS_TOKEN}"
            }
            
            logger.debug(f"Fetching historical data for {symbol} from {from_str} to {to_str}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Failed to fetch historical data: {error_data}")
                    
                    data = await response.json()
                    
                    if data["status"] != "success":
                        raise Exception(f"API returned error: {data}")
                    
                    # Convert candles to HistoricalData objects
                    historical_data = []
                    for candle in data["data"]["candles"]:
                        timestamp = datetime.fromisoformat(candle[0].replace("+0530", ""))
                        historical_data.append(
                            HistoricalData(
                                timestamp=timestamp,
                                open=float(candle[1]),
                                high=float(candle[2]),
                                low=float(candle[3]),
                                close=float(candle[4]),
                                volume=int(candle[5])
                            )
                        )
                    
                    logger.info(f"Fetched {len(historical_data)} candles for {symbol}")
                    return historical_data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            raise

_zerodha_client: Optional[ZerodhaClient] = None

def get_zerodha_client() -> ZerodhaClient:
    """Get or create Zerodha client instance"""
    global _zerodha_client
    if _zerodha_client is None:
        _zerodha_client = ZerodhaClient()
    return _zerodha_client 