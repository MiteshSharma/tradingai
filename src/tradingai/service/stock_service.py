from datetime import datetime, timedelta
import pytz
from typing import List, Tuple, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, and_
from sqlalchemy.orm import Session
from loguru import logger
from dataclasses import asdict

from ..repository.zerodha import ZerodhaClient, get_zerodha_client
from ..domain.models import StockData
from ..domain.stock_analysis import DefaultStockAnalyzer, StockAnalysis
from ..service.instrument_service import InstrumentService
from ..repository.stock_repository import StockRepository
from ..domain.llm_trade import LLMTradeAnalyzer, TradingSignal
from ..config.settings import settings
from ..service.market_service import MarketService

class StockService:
    def __init__(self, db: AsyncSession, zerodha_client: ZerodhaClient):
        self.db = db
        self.zerodha_client = zerodha_client
        self.stock_repo = StockRepository(db)
        self.llm_analyzer = LLMTradeAnalyzer(
            model_name=settings.LLM_MODEL_NAME
        )
        self.instrument_service = InstrumentService(db, None)
        self.market_service = MarketService(db)
    
    async def initialize(self):
        """Initialize service by fetching instruments"""
        await self.instrument_service.fetch_instruments()

    def convert_to_utc(self, dt: datetime) -> datetime:
        """Convert datetime to UTC, handling both naive and timezone-aware datetimes"""
        if dt.tzinfo is None:
            # If naive datetime, assume it's IST
            ist = pytz.timezone('Asia/Kolkata')
            dt = ist.localize(dt)
        return dt.astimezone(pytz.UTC)

    async def get_existing_records(self, symbol: str, from_date: datetime, to_date: datetime) -> set:
        """Get existing records for the symbol within the date range"""
        query = select(StockData.timestamp).where(
            and_(
                StockData.symbol == symbol,
                StockData.timestamp >= from_date,
                StockData.timestamp <= to_date
            )
        )
        result = await self.db.execute(query)
        return {row[0] for row in result.fetchall()}

    async def fetch_and_store_historical_data(
        self, 
        symbols: List[str], 
        from_date: datetime, 
        to_date: datetime
    ) -> int:
        total_records = 0
        
        try:
            # Add debug log
            logger.info(f"Fetching historical data for symbols: {symbols}")
            
            # Validate symbols first
            is_valid, invalid_symbols = await self.instrument_service.validate_symbols(symbols)
            if not is_valid:
                raise ValueError(f"Invalid symbols found: {invalid_symbols}")

            # Get instrument tokens
            for symbol in symbols:
                token = await self.instrument_service.get_instrument_token(symbol)
                if not token:
                    logger.error(f"No instrument token found for {symbol}")
                    raise ValueError(f"No instrument token found for {symbol}")
                logger.info(f"Found token {token} for {symbol}")

            for symbol in symbols:
                try:
                    logger.info(f"Processing symbol: {symbol}")
                    
                    # Get existing records first
                    existing_timestamps = await self.get_existing_records(symbol, from_date, to_date)
                    logger.info(f"Found {len(existing_timestamps)} existing records for {symbol}")
                    
                    # Fetch data from Zerodha
                    stock_data = await self.zerodha_client.fetch_historical_data(
                        symbol, 
                        from_date, 
                        to_date
                    )
                    
                    logger.debug(f"Received {len(stock_data)} records from Zerodha")
                    
                    # Prepare values for insert, skipping existing records
                    values = []
                    skipped = 0
                    for data in stock_data:
                        try:
                            # Convert timestamp to UTC
                            if isinstance(data.timestamp, str):
                                timestamp = datetime.fromisoformat(data.timestamp.replace("+0530", ""))
                                timestamp = self.convert_to_utc(timestamp)
                            else:
                                timestamp = self.convert_to_utc(data.timestamp)
                            
                            # Skip if record already exists
                            if timestamp in existing_timestamps:
                                skipped += 1
                                continue
                            
                            record = {
                                "symbol": str(symbol),
                                "timestamp": timestamp,
                                "open": float(data.open),
                                "high": float(data.high),
                                "low": float(data.low),
                                "close": float(data.close),
                                "volume": int(data.volume),
                                "created_at": datetime.utcnow()
                            }
                            
                            if all(v is not None for v in record.values()):
                                values.append(record)
                            else:
                                logger.warning(f"Skipping record with None values: {record}")
                        except Exception as conv_error:
                            logger.error(f"Data conversion error: {str(conv_error)}")
                            logger.error(f"Problematic record data: {vars(data)}")
                            continue
                    
                    logger.info(f"Skipped {skipped} existing records for {symbol}")
                    
                    if not values:
                        logger.info(f"No new records to insert for {symbol}")
                        continue
                    
                    logger.info(f"Inserting {len(values)} new records for {symbol}")
                    
                    # Insert in smaller batches
                    batch_size = 100
                    for i in range(0, len(values), batch_size):
                        batch = values[i:i + batch_size]
                        try:
                            stmt = insert(StockData).values(batch)
                            await self.db.execute(stmt)
                            await self.db.commit()
                            
                            total_records += len(batch)
                            logger.info(f"Successfully inserted batch of {len(batch)} records")
                        
                        except Exception as insert_error:
                            error_msg = str(insert_error)
                            logger.error(f"Insert error: {error_msg}")
                            logger.error(f"First record in failed batch: {batch[0]}")
                            await self.db.rollback()
                            continue
                    
                    logger.info(f"Completed processing {len(values)} new records for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Error processing symbol {symbol}: {str(e)}")
                    logger.exception("Full traceback:")
                    await self.db.rollback()
                    continue
            
            return total_records 

        except Exception as e:
            logger.error(f"Error processing historical data: {str(e)}")
            logger.exception("Full traceback:")
            await self.db.rollback()
            return 0

    async def fetch_daily_update(self, symbols: List[str]) -> int:
        """
        Fetch last trading day's data. 
        Includes a buffer of 5 days to handle weekends and holidays.
        """
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(days=5)  # 5 days buffer
        
        logger.info(f"Fetching daily update from {start_date} to {end_date}")
        
        return await self.fetch_and_store_historical_data(
            symbols=symbols,
            from_date=start_date,
            to_date=end_date
        ) 

    async def analyze_stock(self, symbol: str) -> StockAnalysis:
        """
        Analyze a stock and return technical analysis results
        """
        try:
            logger.info(f"Starting analysis for {symbol}")
            
            # Check if data exists in DB first
            query = select(StockData).where(StockData.symbol == symbol).limit(1)
            result = await self.db.execute(query)
            exists = result.scalar_one_or_none()
            
            if not exists:
                logger.error(f"No historical data found for {symbol}. Please fetch historical data first.")
                raise ValueError(f"No historical data found for {symbol}. Please fetch historical data first.")
            
            # Get fresh data for analysis
            df = await self.stock_repo.get_stock_data(
                symbol, 
                lookback_days=10,
                ensure_latest=True
            )
            
            if df.empty:
                logger.error(f"Got empty DataFrame for {symbol}")
                raise ValueError(f"No data found for symbol {symbol}")
            
            logger.info(f"Got {len(df)} records for analysis")
            logger.debug(f"Data range: {df.index.min()} to {df.index.max()}")
            
            # Create analyzer and get analysis
            analyzer = DefaultStockAnalyzer(df)
            analysis = analyzer.analyze(symbol)
            
            logger.info(f"Successfully analyzed {symbol}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing stock {symbol}: {str(e)}")
            logger.exception("Full traceback:")
            raise

    async def analyze_stock_with_decision(self, symbol: str) -> Tuple[Dict, TradingSignal]:
        """
        Analyze stock and get LLM trading decision
        Returns:
            Tuple of (analysis_data, trading_signal)
        """
        try:
            # Get stock analysis first
            stock_analysis = await self.analyze_stock(symbol)
            
            # Get market condition with context
            market_condition = self.market_service.get_latest_market_condition()
            
            # Convert StockAnalysis object to dict
            analysis_data = {
                "symbol": stock_analysis.symbol,
                "current_price": stock_analysis.current_price,
                "market_condition": {
                    "direction": market_condition.direction,
                    "score": market_condition.score,
                    "breadth": market_condition.breadth,
                    "context": market_condition.context
                },
                "technical_analysis": {
                    "sma_30_week": stock_analysis.sma_30_week,
                    "is_above_30_week": stock_analysis.is_above_30_week,
                    "macd": {
                        "value": stock_analysis.macd,
                        "signal": stock_analysis.macd_signal,
                        "histogram": stock_analysis.macd_histogram,
                        "is_bullish": stock_analysis.is_bullish_macd
                    },
                    "bollinger_bands": {
                        "upper": stock_analysis.bollinger.upper,
                        "middle": stock_analysis.bollinger.middle,
                        "lower": stock_analysis.bollinger.lower,
                        "monthly_upper": stock_analysis.bollinger.monthly_upper,
                        "is_correction": stock_analysis.bollinger.is_correction
                    },
                    "volume": {
                        "ema_30": stock_analysis.volume_ema_30,
                        "increase_pct": stock_analysis.volume_increase_pct,
                        "is_high": stock_analysis.is_volume_high
                    }
                },
                "last_10_days": [{
                    "date": day.date.isoformat(),
                    "open": day.open,
                    "high": day.high,
                    "low": day.low,
                    "close": day.close,
                    "volume": day.volume
                } for day in stock_analysis.last_10_days]
            }
            
            # Get LLM trading decision
            trading_signal = await self.llm_analyzer.analyze(
                market_data=analysis_data["market_condition"],
                technical_analysis=analysis_data["technical_analysis"],
                price_action=analysis_data["last_10_days"]
            )
            
            # # Store the signal
            # await self.stock_repo.store_trading_signal(
            #     symbol=symbol,
            #     signal=trading_signal,
            #     analysis_data=analysis_data
            # )
            
            return analysis_data, trading_signal
            
        except Exception as e:
            logger.error(f"Error analyzing stock with decision for {symbol}: {str(e)}")
            raise 