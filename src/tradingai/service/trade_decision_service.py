from ..domain.llm_trade import LLMTradeAnalyzer, TradingSignal
from ..repository.trade_repository import TradeRepository
from loguru import logger

class TradeDecisionService:
    def __init__(self, db, model_name: str = "gpt-4o"):
        self.analyzer = LLMTradeAnalyzer(model_name)
        self.trade_repo = TradeRepository(db)
        
    async def get_trading_decision(self, stock_analysis: dict) -> TradingSignal:
        """Get trading decision for a stock"""
        try:
            # Extract required data
            market_data = stock_analysis["market_condition"]
            technical_analysis = stock_analysis["technical_analysis"]
            price_action = stock_analysis["last_10_days"]
            
            # Get decision from LLM
            signal = await self.analyzer.analyze(
                market_data,
                technical_analysis,
                price_action
            )
            
            # Store the signal
            await self.trade_repo.store_signal(
                symbol=stock_analysis["symbol"],
                signal=signal
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error getting trading decision: {str(e)}")
            raise 