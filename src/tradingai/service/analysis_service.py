from datetime import datetime
from typing import Dict, List
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .market_service import MarketService
from .stock_service import StockService
from ..repository.zerodha import ZerodhaClient
from ..repository.instrument_repository import InstrumentRepository
from ..service.instrument_service import InstrumentService
from ..domain.market_analysis import MarketCondition
from ..domain.stock_analysis import StockAnalysis

class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Initialize required services
        instrument_repo = InstrumentRepository()
        instrument_service = InstrumentService(db, instrument_repo)
        zerodha_client = ZerodhaClient(instrument_service)
        
        self.market_service = MarketService(db)
        self.stock_service = StockService(db, zerodha_client)
    
    async def analyze_stock(self, symbol: str) -> Dict:
        """
        Comprehensive stock analysis combining market conditions and technical analysis
        """
        try:
            # Get market condition
            market_condition = self.market_service.get_latest_market_condition()
            if not market_condition:
                raise ValueError("Market condition not available. Please run market analysis first.")
            
            # Get stock analysis
            stock_analysis = await self.stock_service.analyze_stock(symbol)
            
            # Format response
            return {
                "symbol": symbol,
                "current_price": stock_analysis.current_price,
                "market_condition": {
                    "direction": market_condition.direction.value,
                    "score": market_condition.score,
                    "breadth": market_condition.breadth
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
            
        except ValueError as e:
            logger.warning(f"Validation error analyzing {symbol}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            logger.exception("Full traceback:")
            raise 