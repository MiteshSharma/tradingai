from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from ..domain.models import StockData
from loguru import logger
import pytz

class StockRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_stock_data(
        self, 
        symbol: str, 
        lookback_days: int = 365,
        ensure_latest: bool = True
    ) -> pd.DataFrame:
        """Get stock data from database"""
        try:
            end_date = datetime.now(pytz.UTC)
            start_date = end_date - timedelta(days=lookback_days)
            
            logger.info(f"Fetching data for {symbol} from {start_date} to {end_date}")
            
            # Get data
            query = select(StockData).where(
                and_(
                    StockData.symbol == symbol,
                    StockData.timestamp >= start_date,
                    StockData.timestamp <= end_date
                )
            ).order_by(StockData.timestamp.desc())
            
            # Debug query
            logger.debug(f"Query: {query}")
            
            result = await self.db.execute(query)
            records = result.scalars().all()
            
            # Log record count
            logger.info(f"Found {len(records) if records else 0} records for {symbol}")
            
            if not records:
                logger.warning(f"No data found in DB for {symbol}")
                return pd.DataFrame()
                
            # Convert to dataframe
            df = pd.DataFrame([{
                'timestamp': r.timestamp,
                'open': r.open,
                'high': r.high,
                'low': r.low,
                'close': r.close,
                'volume': r.volume
            } for r in records])
            
            # Log dataframe info
            logger.info(f"DataFrame shape: {df.shape}")
            logger.info(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            
            if ensure_latest:
                # Check if latest data is from today or yesterday (for market holidays)
                latest_date = df['timestamp'].max()
                days_old = (end_date - latest_date).days
                
                if days_old > 2:  # Data is older than 2 days
                    logger.warning(f"Latest data for {symbol} is {days_old} days old")
            
            # Set timestamp as index and sort
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {str(e)}")
            logger.exception("Full traceback:")
            raise 