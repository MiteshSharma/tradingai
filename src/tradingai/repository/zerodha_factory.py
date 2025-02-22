from loguru import logger
from ..config.settings import settings
from .zerodha import ZerodhaClient
from .mock_zerodha import MockZerodhaClient

def get_zerodha_client():
    if settings.USE_MOCK_ZERODHA:
        logger.info("Using Mock Zerodha Client")
        return MockZerodhaClient()
    else:
        logger.info("Using Real Zerodha Client")
        return ZerodhaClient() 