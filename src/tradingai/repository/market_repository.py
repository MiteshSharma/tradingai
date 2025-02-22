from datetime import date
from sqlalchemy.orm import Session
from tradingai.domain.models import MarketConditionModel
from tradingai.domain.market_analysis import MarketCondition

class MarketRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_market_condition(self, condition: MarketCondition) -> MarketConditionModel:
        """Save market condition to database"""
        db_condition = MarketConditionModel(
            date=condition.date,
            direction=condition.direction.value,
            score=condition.score,
            breadth=condition.breadth
        )
        
        # Check if entry for date exists
        existing = self.db.query(MarketConditionModel).filter(
            MarketConditionModel.date == condition.date
        ).first()
        
        if existing:
            # Update existing
            existing.direction = condition.direction.value
            existing.score = condition.score
            existing.breadth = condition.breadth
            self.db.commit()
            return existing
        
        # Create new
        self.db.add(db_condition)
        self.db.commit()
        self.db.refresh(db_condition)
        return db_condition

    def get_latest_condition(self) -> MarketCondition:
        """Get the most recent market condition"""
        result = self.db.query(MarketConditionModel).order_by(
            MarketConditionModel.date.desc()
        ).first()
        
        if not result:
            return None
            
        return MarketCondition(
            date=result.date,
            direction=result.direction,
            score=result.score,
            breadth=result.breadth
        ) 