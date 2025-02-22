from loguru import logger
from ..config.settings import settings
from ..repository.database import AsyncSessionLocal
from ..repository.zerodha import ZerodhaClient
from ..service.stock_service import StockService

async def run_daily_update():
    """Run daily update for all configured symbols"""
    try:
        async with AsyncSessionLocal() as db:
            zerodha_client = ZerodhaClient()
            service = StockService(db, zerodha_client)
            
            total_records = await service.fetch_daily_update(
                symbols=settings.VALID_SYMBOLS
            )
            
            logger.info(f"Daily update complete. Added {total_records} new records")
            
    except Exception as e:
        logger.error(f"Daily update failed: {str(e)}")
        logger.exception("Full traceback:")
        raise 