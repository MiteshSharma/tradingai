from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Security, Request
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from pydantic import BaseModel

from src.tradingai.service.stock_service import StockService

from ..repository.database import get_db
from ..service.analysis_service import AnalysisService
from ..domain.validators import HistoricalDataRequest
from ..tasks.daily_update import run_daily_update
from ..config.settings import settings
from fastapi.security import APIKeyHeader
from ..repository.instrument_repository import InstrumentRepository
from ..service.instrument_service import InstrumentService
from ..repository.zerodha import ZerodhaClient
from ..domain.llm_trade import TradingSignal

router = APIRouter(prefix="/stock", tags=["stock"])

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

class StockAnalysisResponse(BaseModel):
    symbol: str
    current_price: float
    market_condition: dict
    technical_analysis: dict
    last_10_days: List[dict]

class StockAnalysisWithDecisionResponse(BaseModel):
    analysis: StockAnalysisResponse
    trading_signal: TradingSignal

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Could not validate API key"
        )
    return api_key

@router.get("/analyze/{symbol}")
async def analyze_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db)
) -> StockAnalysisResponse:
    """
    Analyze a stock by getting market conditions and technical analysis
    """
    try:
        analysis_service = AnalysisService(db)
        try:
            result = await analysis_service.analyze_stock(symbol)
            return StockAnalysisResponse(**result)
        except ValueError as e:
            if "Invalid symbol" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail={"error": "Invalid symbol", "symbol": symbol}
                )
            raise
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze/{symbol}/with-decision")
async def analyze_stock_with_decision(
    symbol: str,
    db: AsyncSession = Depends(get_db)
) -> StockAnalysisWithDecisionResponse:
    """
    Analyze a stock and get trading decision
    """
    try:
        # Initialize services
        instrument_repo = InstrumentRepository()
        instrument_service = InstrumentService(db, instrument_repo)
        zerodha_client = ZerodhaClient(instrument_service)
        stock_service = StockService(db, zerodha_client)
        
        # Get analysis and decision
        analysis_data, trading_signal = await stock_service.analyze_stock_with_decision(symbol)
        
        return StockAnalysisWithDecisionResponse(
            analysis=StockAnalysisResponse(**analysis_data),
            trading_signal=trading_signal
        )
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stocks/historical")
async def fetch_historical_data(
    request: Request,
    historical_request: HistoricalDataRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Fetch and store historical data for symbols"""
    # Debug incoming request
    logger.info(f"Received request at: {request.url}")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {request.headers}")
    logger.info(f"Historical request data: {historical_request}")
    
    try:
        instrument_repo = InstrumentRepository()
        instrument_service = InstrumentService(db, instrument_repo)
        zerodha_client = ZerodhaClient(instrument_service)
        stock_service = StockService(db, zerodha_client)
        
        try:
            logger.info(f"Valid symbols in DB: {historical_request.symbols}")
            total_records = await stock_service.fetch_and_store_historical_data(
                historical_request.symbols,
                historical_request.from_date,
                historical_request.to_date
            )
            
            return {
                "status": "success",
                "message": f"Successfully fetched and stored {total_records} records",
                "total_records": total_records
            }
            
        except ValueError as e:
            # Return invalid symbols in response
            return {
                "status": "error",
                "message": str(e),
                "invalid_symbols": str(e).split(": ")[1].strip("[]").split(", ")
            }
            
    except Exception as e:
        logger.error(f"Error in fetch_historical_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stocks/daily-update")
async def trigger_daily_update(
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
) -> dict:
    """
    Trigger daily update for all configured symbols.
    This runs asynchronously in the background.
    """
    try:
        # Add the task to background tasks
        background_tasks.add_task(run_daily_update)
        
        return {
            "status": "success",
            "message": "Daily update task started"
        }
        
    except Exception as e:
        logger.error(f"Error triggering daily update: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger daily update: {str(e)}"
        )

@router.get("/symbols")
async def get_all_symbols(
    db: AsyncSession = Depends(get_db)
) -> List[str]:
    """Get all available trading symbols"""
    try:
        instrument_service = InstrumentService(db, None)
        return await instrument_service.get_all_symbols()
    except Exception as e:
        logger.error(f"Error getting symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 