from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import date, datetime
import pandas as pd
import numpy as np
from typing import Protocol

@dataclass
class DailyData:
    date: datetime
    open: float
    close: float
    high: float
    low: float
    volume: int

@dataclass
class BollingerBands:
    upper: float
    middle: float
    lower: float
    monthly_upper: float
    is_correction: bool  # True if price is between monthly upper and daily lower

@dataclass
class StockAnalysis:
    symbol: str
    current_price: float
    sma_30_week: float
    is_above_30_week: bool
    macd: float
    macd_signal: float
    macd_histogram: float
    is_bullish_macd: bool
    bollinger: BollingerBands
    volume_ema_30: float
    volume_increase_pct: float
    is_volume_high: bool
    last_10_days: List[DailyData]

class StockAnalyzer(Protocol):
    """Interface for stock analysis implementations"""
    
    def analyze(self, symbol: str) -> StockAnalysis:
        """Analyze a stock and return analysis results"""
        pass

class DefaultStockAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def calculate_macd(self, fast=12, slow=26, signal=9):
        """Calculate MACD for daily timeframe"""
        # Calculate exponential moving averages
        exp1 = self.df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = self.df['close'].ewm(span=slow, adjust=False).mean()
        
        # Calculate MACD line
        macd = exp1 - exp2
        
        # Calculate signal line
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd - signal_line
        
        return macd.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
    
    def analyze(self, symbol: str) -> StockAnalysis:
        """
        Analyze stock data and return technical analysis results
        """
        try:
            if self.df.empty:
                raise ValueError(f"No data available for {symbol}")

            # Get current price (last close)
            current_price = float(self.df['close'].iloc[-1])
            
            # Calculate 30-week SMA (using ~150 trading days)
            sma_30_week = float(self.df['close'].rolling(window=150).mean().iloc[-1])
            is_above_30_week = bool(current_price > sma_30_week)
            
            # Calculate MACD
            macd_line, signal_line, histogram = self.calculate_macd()
            is_bullish_macd = bool(histogram > 0)
            
            # Calculate volume indicators
            volume_ema_30 = float(self.df['volume'].ewm(span=30).mean().iloc[-1])
            avg_volume = float(self.df['volume'].mean())
            volume_increase_pct = float(((self.df['volume'].iloc[-1] - avg_volume) / avg_volume) * 100)
            is_volume_high = bool(self.df['volume'].iloc[-1] > volume_ema_30)
            
            # Get last 10 days of data
            last_10_days = []
            for idx in range(min(10, len(self.df))):
                row = self.df.iloc[-(idx+1)]
                last_10_days.append(DailyData(
                    date=row.name,  # timestamp is the index
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume']
                ))
            
            # Calculate Bollinger Bands
            bb_period = 20
            std_dev = 2
            
            middle_band = self.df['close'].rolling(window=bb_period).mean()
            std = self.df['close'].rolling(window=bb_period).std()
            
            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)
            
            # Monthly upper band (for resistance)
            monthly_upper = self.df['high'].resample('M').max().iloc[-1]
            
            # Check if in correction (price below middle band)
            is_correction = bool(current_price < middle_band.iloc[-1])
            
            bollinger = BollingerBands(
                upper=upper_band.iloc[-1],
                middle=middle_band.iloc[-1],
                lower=lower_band.iloc[-1],
                monthly_upper=monthly_upper,
                is_correction=is_correction
            )
            
            return StockAnalysis(
                symbol=symbol,
                current_price=current_price,
                sma_30_week=sma_30_week,
                is_above_30_week=is_above_30_week,
                macd=float(macd_line),
                macd_signal=float(signal_line),
                macd_histogram=float(histogram),
                is_bullish_macd=is_bullish_macd,
                volume_ema_30=volume_ema_30,
                volume_increase_pct=volume_increase_pct,
                is_volume_high=is_volume_high,
                bollinger=bollinger,
                last_10_days=last_10_days
            )

        except Exception as e:
            raise ValueError(f"Error analyzing {symbol}: {str(e)}")