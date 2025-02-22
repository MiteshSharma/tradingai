from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
from ..domain.models import Base

async def init_database(engine: AsyncEngine):
    """Initialize database tables"""
    try:
        # Test connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
        
        # Create tables if they don't exist
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            # Only create tables if they don't exist
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise 