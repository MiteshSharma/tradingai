from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..repository.database import get_db
from ..service.instrument_service import InstrumentService
from ..repository.instrument_repository import InstrumentRepository

router = APIRouter(tags=["instruments"])

@router.post("/instruments/fetch")
async def fetch_instruments(
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch and store instruments from Zerodha
    This should be called once at the start of the trading day
    """
    try:
        instrument_repo = InstrumentRepository()
        instrument_service = InstrumentService(db, instrument_repo)
        
        await instrument_service.fetch_instruments()
        
        return {
            "status": "success",
            "message": "Successfully fetched and stored instruments"
        }
        
    except Exception as e:
        logger.error(f"Error fetching instruments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch instruments: {str(e)}"
        )

@router.get("/instruments/search/{symbol}")
async def search_instrument(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """Search for an instrument by symbol"""
    try:
        instrument_repo = InstrumentRepository()
        instrument_service = InstrumentService(db, instrument_repo)
        
        token = await instrument_service.get_instrument_token(symbol)
        if not token:
            raise HTTPException(
                status_code=404,
                detail=f"Instrument not found: {symbol}"
            )
            
        return {
            "symbol": symbol,
            "instrument_token": token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching instrument: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search instrument: {str(e)}"
        ) 