from datetime import datetime
import csv
from io import StringIO
import aiohttp
from typing import List, Dict
from loguru import logger

from ..config.settings import settings

class InstrumentRepository:
    def __init__(self):
        self.base_url = "https://api.kite.trade"

    async def fetch_instruments(self) -> List[Dict]:
        """Fetch instruments from Zerodha API"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-Kite-Version": "3",
                    "Authorization": f"token {settings.ZERODHA_API_KEY}:{settings.ZERODHA_ACCESS_TOKEN}"
                }
                async with session.get(f"{self.base_url}/instruments", headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch instruments: {response.status}")
                    
                    # Parse CSV data
                    csv_data = StringIO(await response.text())
                    reader = csv.DictReader(csv_data)
                    
                    instruments = []
                    for row in reader:
                        if row['segment'] in ['NSE']:  # Filter for NSE equity
                            instrument = {
                                "instrument_token": int(row['instrument_token']),
                                "exchange_token": int(row['exchange_token']),
                                "tradingsymbol": row['tradingsymbol'],
                                "name": row['name'],
                                "exchange": row['exchange'],
                                "segment": row['segment'],
                                "instrument_type": row['instrument_type'],
                                "tick_size": float(row['tick_size']),
                                "lot_size": int(row['lot_size']),
                                "created_at": datetime.utcnow()
                            }
                            instruments.append(instrument)
                    
                    return instruments
                    
        except Exception as e:
            logger.error(f"Error fetching instruments: {str(e)}")
            raise 