from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from ..domain.models import MarketConditionModel
from ..domain.market_analysis import MarketCondition, MarketDirection

class MarketService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def get_latest_market_condition(self) -> MarketCondition:
        """Get the latest market condition"""
        try:
            # For now, return a default condition
            # TODO: Implement actual market analysis
            score = 5  # Example score
            direction = MarketDirection.BULLISH
            breadth = 0.5

            # Generate context based on conditions
            context = self._generate_market_context(direction, score, breadth)
            
            return MarketCondition(
                direction=direction,
                score=score,
                breadth=breadth,
                date=date.today(),
                context=context
            )
        except Exception as e:
            logger.error(f"Error getting market condition: {str(e)}")
            raise
            
    def _generate_market_context(self, direction: MarketDirection, score: int, breadth: float) -> str:
        """Generate detailed market context"""
        
        # Direction explanation
        direction_context = {
            MarketDirection.BULLISH: "Market is in bullish trend showing upward momentum",
            MarketDirection.BEARISH: "Market is in bearish trend showing downward pressure",
            MarketDirection.NEUTRAL: "Market is in neutral trend showing sideways movement"
        }[direction]
        
        # Score explanation (6 to -6)
        score_meanings = {
            range(4, 7): "Very Bullish: Strong uptrend with multiple EMAs aligned upward",
            range(2, 4): "Moderately Bullish: Uptrend with some positive EMA crossovers",
            range(0, 2): "Slightly Bullish: Early signs of upward movement",
            range(-2, 0): "Slightly Bearish: Early signs of downward movement",
            range(-4, -2): "Moderately Bearish: Downtrend with some negative EMA crossovers",
            range(-7, -4): "Very Bearish: Strong downtrend with multiple EMAs aligned downward"
        }
        
        score_context = next(
            desc for score_range, desc in score_meanings.items() 
            if score in score_range
        )
        
        # Score calculation explanation
        score_calc = """
        Score is calculated using 6 EMA rules (+1/-1 each):
        1. EMA10 > EMA20
        2. EMA10 > EMA50
        3. EMA10 > EMA200
        4. EMA20 > EMA50
        5. EMA20 > EMA200
        6. EMA50 > EMA200
        """
        
        # Breadth explanation
        breadth_context = f"Market breadth is {breadth:.1%}, indicating "
        if breadth > 0.6:
            breadth_context += "strong market participation with majority stocks advancing"
        elif breadth > 0.4:
            breadth_context += "balanced market participation"
        else:
            breadth_context += "weak market participation with majority stocks declining"
            
        return f"""Market Analysis:
1. Direction: {direction_context}
2. Score ({score}/6): {score_context}
3. {breadth_context}

Technical Details:
{score_calc}
""" 