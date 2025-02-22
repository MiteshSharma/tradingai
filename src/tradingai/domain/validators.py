from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from ..config.settings import settings

MAX_DATE_RANGE_YEARS = 3
MAX_SYMBOLS_PER_REQUEST = 5

class HistoricalDataRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    symbols: List[str]
    from_date: datetime
    to_date: datetime
    
    @field_validator('to_date')
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        if 'from_date' in info.data:
            # Check if date range is valid
            if v < info.data['from_date']:
                raise ValueError("to_date must be greater than from_date")
            
            # Check if date range is within limits
            date_range = v - info.data['from_date']
            max_range = timedelta(days=MAX_DATE_RANGE_YEARS * 365)
            if date_range > max_range:
                raise ValueError(f"Date range cannot exceed {MAX_DATE_RANGE_YEARS} years")
        
        if v > datetime.now():
            raise ValueError("to_date cannot be in the future")
        return v 