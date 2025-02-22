from datetime import datetime, timedelta
import random
import pytz

IST = pytz.timezone('Asia/Kolkata')

def generate_mock_candle(date: datetime, base_price: float = 1700.0) -> list:
    """Generate a single mock candle with realistic OHLCV data"""
    # Create random price movements within 1% of base price
    variation = base_price * 0.01
    open_price = base_price + random.uniform(-variation, variation)
    high_price = open_price + random.uniform(0, variation)
    low_price = open_price - random.uniform(0, variation)
    close_price = random.uniform(low_price, high_price)
    volume = random.randint(500, 3000)
    
    return [
        date.astimezone(IST).isoformat(),
        round(open_price, 2),
        round(high_price, 2),
        round(low_price, 2),
        round(close_price, 2),
        volume
    ]

def get_mock_historical_data(symbol: str, from_date: datetime, to_date: datetime) -> dict:
    """Generate mock historical data for given date range"""
    candles = []
    current_date = from_date
    base_price = 1700.0  # Starting price
    
    while current_date <= to_date:
        # Generate data for trading days (Monday to Friday)
        if current_date.weekday() < 5:  # 0-4 represents Monday to Friday
            # Generate candles for trading hours (9:15 AM to 3:30 PM)
            trading_start = current_date.replace(hour=9, minute=15)
            trading_end = current_date.replace(hour=15, minute=30)
            current_time = trading_start
            
            while current_time <= trading_end:
                candle = generate_mock_candle(current_time, base_price)
                candles.append(candle)
                base_price = candle[4]  # Use last close as next base price
                current_time += timedelta(minutes=1)
        
        current_date += timedelta(days=1)
    
    return {
        "status": "success",
        "data": {
            "candles": candles
        }
    } 