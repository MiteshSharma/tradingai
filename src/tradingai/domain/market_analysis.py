from enum import Enum
from datetime import date
from pydantic import BaseModel
from typing import Optional

class MarketDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

class MarketCondition(BaseModel):
    direction: MarketDirection
    score: int
    breadth: Optional[float] = None
    date: date
    context: Optional[str] = None

class MarketAnalysis(BaseModel):
    condition: MarketCondition
    nifty_trend: dict
    sector_performance: dict
    market_breadth: dict

    def calculate_market_score(self) -> int:
        """Calculate market score based on EMA rules (+6 to -6)"""
        df = self.index_data.copy()
        
        # Calculate EMAs
        df['EMA10'] = df['close'].ewm(span=10, adjust=False).mean()
        df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # Get latest values
        latest = df.iloc[-1]
        
        score = 0
        # EMA10 rules
        if latest['EMA10'] > latest['EMA20']:
            score += 1
        else:
            score -= 1
            
        if latest['EMA10'] > latest['EMA50']:
            score += 1
        else:
            score -= 1
            
        if latest['EMA10'] > latest['EMA200']:
            score += 1
        else:
            score -= 1
            
        # EMA20 rules
        if latest['EMA20'] > latest['EMA50']:
            score += 1
        else:
            score -= 1
            
        if latest['EMA20'] > latest['EMA200']:
            score += 1
        else:
            score -= 1
            
        # EMA50 rule
        if latest['EMA50'] > latest['EMA200']:
            score += 1
        else:
            score -= 1
            
        return score

    def get_market_direction(self) -> MarketDirection:
        """Determine market direction based on score"""
        score = self.calculate_market_score()
        
        if score >= 2:
            return MarketDirection.BULLISH
        elif score <= -2:
            return MarketDirection.BEARISH
        else:
            return MarketDirection.NEUTRAL

    def get_market_condition(self) -> MarketCondition:
        """Get complete market condition including direction and score"""
        score = self.calculate_market_score()
        direction = self.get_market_direction()
        
        return MarketCondition(
            date=date.today(),
            direction=direction,
            score=score
        ) 