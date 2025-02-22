from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class StockData(Base):
    __tablename__ = "stock_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(32), index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"StockData(symbol={self.symbol}, timestamp={self.timestamp})"

    class Config:
        orm_mode = True

class Instrument(Base):
    __tablename__ = "instruments"
    
    id = Column(Integer, primary_key=True, index=True)
    instrument_token = Column(Integer, unique=True, nullable=False)
    exchange_token = Column(Integer)
    tradingsymbol = Column(String(32), index=True, nullable=False)
    name = Column(String(100))
    exchange = Column(String(10), nullable=False)
    segment = Column(String(10))
    instrument_type = Column(String(10))
    tick_size = Column(Float)
    lot_size = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    class Config:
        orm_mode = True

class MarketConditionModel(Base):
    __tablename__ = 'market_conditions'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, unique=True)
    direction = Column(SQLEnum('BULLISH', 'BEARISH', 'NEUTRAL', name='market_direction'), nullable=False)
    score = Column(Integer, nullable=False)
    breadth = Column(Float, nullable=True)

    def __repr__(self):
        return f"<MarketCondition(date={self.date}, direction={self.direction}, score={self.score})>" 