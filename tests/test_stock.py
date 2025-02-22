import pytest
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd

from tradingai.service.stock_service import StockService
from tradingai.domain.stock_analysis import StockAnalysis, DailyData, BollingerBands
from tradingai.domain.market_analysis import MarketDirection
from tradingai.domain.llm_trade import TradingSignal

@pytest.fixture
def mock_db():
    mock = AsyncMock(spec=AsyncSession)
    # Mock execute to return a result that has scalars() and all()
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = []
    mock.execute.return_value = mock_result
    return mock

@pytest.fixture
def mock_zerodha_client():
    return AsyncMock()

@pytest.fixture
def stock_service(mock_db, mock_zerodha_client):
    service = StockService(mock_db, mock_zerodha_client)
    # Mock stock_repo's get_stock_data to return DataFrame
    service.stock_repo.get_stock_data = AsyncMock(return_value=pd.DataFrame())
    return service

@pytest.mark.asyncio
async def test_fetch_historical_data_success(stock_service):
    """Test successful historical data fetch"""
    # Setup
    symbols = ["ZOTA"]
    from_date = datetime.now(pytz.UTC) - timedelta(days=10)
    to_date = datetime.now(pytz.UTC)
    
    # Mock instrument service
    stock_service.instrument_service.get_instrument_token = AsyncMock(return_value=12345)
    stock_service.instrument_service.validate_symbols = AsyncMock(return_value=(True, []))
    
    # Mock get_existing_records to return empty set
    stock_service.get_existing_records = AsyncMock(return_value=set())
    
    # Mock zerodha response
    mock_data = AsyncMock()
    mock_data.timestamp = datetime.now(pytz.UTC)
    mock_data.open = 100.0
    mock_data.high = 105.0
    mock_data.low = 98.0
    mock_data.close = 102.0
    mock_data.volume = 10000
    
    stock_service.zerodha_client.fetch_historical_data = AsyncMock(return_value=[mock_data])
    
    # Mock successful DB insert
    mock_result = AsyncMock()
    stock_service.db.execute = AsyncMock(return_value=mock_result)
    stock_service.db.commit = AsyncMock()
    
    # Execute
    total_records = await stock_service.fetch_and_store_historical_data(
        symbols, from_date, to_date
    )
    
    # Assert
    assert total_records == 1  # One record inserted
    assert stock_service.zerodha_client.fetch_historical_data.called
    assert stock_service.db.commit.called

@pytest.mark.asyncio
async def test_analyze_stock_success(stock_service):
    """Test successful stock analysis"""
    # Setup
    symbol = "ZOTA"
    
    # Mock DB check
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = True
    stock_service.db.execute.return_value = mock_result
    
    # Mock DataFrame
    mock_df = pd.DataFrame({
        'timestamp': [datetime.now(pytz.UTC)],
        'open': [100.0],
        'high': [105.0],
        'low': [98.0],
        'close': [102.0],
        'volume': [10000]
    })
    stock_service.stock_repo.get_stock_data.return_value = mock_df
    
    with patch('tradingai.service.stock_service.DefaultStockAnalyzer') as mock_analyzer:
        # Mock analyzer response
        mock_analyzer.return_value.analyze.return_value = StockAnalysis(
            symbol=symbol,
            current_price=100.0,
            sma_30_week=95.0,
            is_above_30_week=True,
            macd=2.0,
            macd_signal=1.0,
            macd_histogram=1.0,
            is_bullish_macd=True,
            volume_ema_30=50000,
            volume_increase_pct=10.0,
            is_volume_high=True,
            bollinger=BollingerBands(
                upper=105.0,
                middle=100.0,
                lower=95.0,
                monthly_upper=110.0,
                is_correction=False
            ),
            last_10_days=[
                DailyData(
                    date=datetime.now(pytz.UTC).date(),
                    open=100.0,
                    high=105.0,
                    low=98.0,
                    close=102.0,
                    volume=10000
                )
            ]
        )
        
        # Execute
        analysis = await stock_service.analyze_stock(symbol)
        
        # Assert
        assert analysis.symbol == symbol
        assert analysis.current_price == 100.0
        assert analysis.is_above_30_week is True
        assert analysis.is_bullish_macd is True
        assert len(analysis.last_10_days) == 1

@pytest.mark.asyncio
async def test_analyze_stock_with_decision(stock_service):
    """Test stock analysis with LLM decision"""
    # Setup
    symbol = "ZOTA"
    
    # Mock analysis response
    mock_analysis = StockAnalysis(
        symbol=symbol,
        current_price=100.0,
        sma_30_week=95.0,
        is_above_30_week=True,
        macd=2.0,
        macd_signal=1.0,
        macd_histogram=1.0,
        is_bullish_macd=True,
        volume_ema_30=50000,
        volume_increase_pct=10.0,
        is_volume_high=True,
        bollinger=BollingerBands(
            upper=105.0,
            middle=100.0,
            lower=95.0,
            monthly_upper=110.0,
            is_correction=False
        ),
        last_10_days=[
            DailyData(
                date=datetime.now(pytz.UTC).date(),
                open=100.0,
                high=105.0,
                low=98.0,
                close=102.0,
                volume=10000
            )
        ]
    )
    
    # Mock LLM response
    mock_signal = TradingSignal(
        decision="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        allocation_percentage=5.0,
        reasoning=["Strong uptrend", "High volume"]
    )
    
    with patch.object(stock_service, 'analyze_stock', return_value=mock_analysis), \
         patch.object(stock_service.llm_analyzer, 'analyze', return_value=mock_signal):
        
        # Execute
        analysis_data, trading_signal = await stock_service.analyze_stock_with_decision(symbol)
        
        # Assert
        assert analysis_data["symbol"] == symbol
        assert analysis_data["current_price"] == 100.0
        assert trading_signal.decision == "BUY"
        assert trading_signal.entry_price == 100.0
        assert len(trading_signal.reasoning) == 2

@pytest.mark.asyncio
async def test_fetch_historical_data_invalid_symbol(stock_service):
    """Test historical data fetch with invalid symbol"""
    # Setup
    symbols = ["INVALID"]
    from_date = datetime.now(pytz.UTC) - timedelta(days=10)
    to_date = datetime.now(pytz.UTC)
    
    # Mock validation to fail first (since it's checked before token)
    stock_service.instrument_service.validate_symbols = AsyncMock(return_value=(False, symbols))
    
    # Execute and Assert
    with pytest.raises(ValueError) as exc_info:
        await stock_service.fetch_and_store_historical_data(
            symbols, from_date, to_date
        )
    assert "Invalid symbols found: ['INVALID']" in str(exc_info.value)

@pytest.mark.asyncio
async def test_analyze_stock_no_data(stock_service):
    """Test stock analysis with no data"""
    # Mock DB check to return None
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    stock_service.db.execute.return_value = mock_result
    
    with pytest.raises(ValueError) as exc_info:
        await stock_service.analyze_stock("NOSYMBOL")
    assert "No historical data found" in str(exc_info.value) 