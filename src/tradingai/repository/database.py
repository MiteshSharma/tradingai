from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from loguru import logger
from ..config.settings import settings
from .database_init import init_database

# Simplified connection URL first
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

logger.info(f"Connecting to database: {DATABASE_URL}")

async def test_connection():
    import asyncpg
    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT
        )
        await conn.execute('SELECT 1')
        await conn.close()
        logger.info("Direct asyncpg connection test successful")
    except Exception as e:
        logger.error(f"Direct asyncpg connection test failed: {str(e)}")
        raise

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Enable full SQL logging
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def init_models():
    """Initialize database models on startup"""
    try:
        await test_connection()  # Test direct connection first
        await init_database(engine)
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

async def get_db():
    try:
        async with AsyncSessionLocal() as db:
            try:
                logger.debug("Creating new database session")
                # Test the connection
                await db.execute("SELECT 1")
                yield db
            except Exception as e:
                logger.error(f"Database session error: {str(e)}")
                raise
            finally:
                logger.debug("Closing database session")
                await db.close()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise 