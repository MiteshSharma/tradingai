from datetime import datetime
import csv
from io import StringIO
import aiohttp
from typing import Dict, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from ..domain.models import Instrument
from ..repository.instrument_repository import InstrumentRepository

class InstrumentService:
    def __init__(self, db: AsyncSession, instrument_repository: InstrumentRepository):
        self.db = db
        self.repository = instrument_repository
        self.instruments_cache: Dict[str, int] = {}  # symbol -> token mapping
        
    async def fetch_instruments(self) -> None:
        """Fetch instruments from repository and store in database"""
        try:
            instruments = await self.repository.fetch_instruments()
            
            # Update cache
            for instrument in instruments:
                self.instruments_cache[instrument['tradingsymbol']] = instrument['instrument_token']
            
            # Bulk insert/update instruments
            await self.update_instruments(instruments)
            
            logger.info(f"Successfully updated {len(instruments)} instruments")
            
        except Exception as e:
            logger.error(f"Error updating instruments: {str(e)}")
            raise

    async def update_instruments(self, instruments: list) -> None:
        """Update instruments in database"""
        try:
            # Insert new instruments, update if exists
            for instrument in instruments:
                await self.db.merge(Instrument(**instrument))
            await self.db.commit()
            
            logger.info(f"Updated {len(instruments)} instruments")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating instruments: {str(e)}")
            raise

    async def get_instrument_token(self, symbol: str) -> Optional[int]:
        """Get instrument token for a symbol"""
        try:
            # Try cache first
            logger.debug(f"Looking up token for symbol: {symbol}")
            if symbol in self.instruments_cache:
                logger.debug(f"Found in cache: {symbol} -> {self.instruments_cache[symbol]}")
                return self.instruments_cache[symbol]
            
            # Try database
            logger.debug(f"Cache miss, querying database for: {symbol}")
            query = select(Instrument.instrument_token).where(Instrument.tradingsymbol == symbol)
            result = await self.db.execute(query)
            token = result.scalar_one_or_none()
            
            if token:
                logger.debug(f"Found in DB: {symbol} -> {token}")
                self.instruments_cache[symbol] = token
                return token
            
            logger.warning(f"No token found for symbol: {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting instrument token for {symbol}: {str(e)}")
            logger.exception("Full token lookup error traceback:")
            raise

    async def refresh_cache(self) -> None:
        """Refresh the instruments cache from database"""
        try:
            logger.debug("Refreshing instruments cache")
            query = select(Instrument.tradingsymbol, Instrument.instrument_token)
            result = await self.db.execute(query)
            self.instruments_cache = {row[0]: row[1] for row in result.fetchall()}
            logger.debug(f"Cache refreshed with {len(self.instruments_cache)} instruments")
            
        except Exception as e:
            logger.error("Error refreshing cache")
            logger.exception("Full cache refresh error traceback:")
            raise

    async def get_all_symbols(self) -> List[str]:
        """Get all trading symbols from database"""
        try:
            query = select(Instrument.tradingsymbol)
            result = await self.db.execute(query)
            symbols = [row[0] for row in result.scalars().all()]
            logger.info(f"Found {len(symbols)} symbols in database")
            return symbols
        except Exception as e:
            logger.error(f"Error getting symbols: {str(e)}")
            raise

    async def validate_symbols(self, symbols: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate symbols against instrument database
        Returns:
            Tuple of (is_valid, invalid_symbols)
        """
        try:
            # Get all valid symbols from DB
            valid_symbols = await self.get_all_symbols()
            
            # Find invalid symbols with case-insensitive comparison
            invalid_symbols = []
            for symbol in symbols:
                if symbol.upper() not in {s.upper() for s in valid_symbols}:
                    invalid_symbols.append(symbol)
            
            is_valid = len(invalid_symbols) == 0
            return is_valid, invalid_symbols
            
        except Exception as e:
            logger.error(f"Error validating symbols: {str(e)}")
            raise 