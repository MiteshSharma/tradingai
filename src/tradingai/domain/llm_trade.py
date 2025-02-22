from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from enum import Enum

from ..config.settings import settings
from ..config.prompts.swing_trader import SWING_TRADER_PROMPT

class TradeDecision(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class TradingSignal(BaseModel):
    decision: TradeDecision = Field(description="Trading decision (BUY/SELL/HOLD)")
    entry_price: Optional[float] = Field(description="Suggested entry price")
    stop_loss: Optional[float] = Field(description="Suggested stop loss price")
    allocation_percentage: Optional[float] = Field(description="Suggested position size (0-100)")
    reasoning: List[str] = Field(description="List of reasons for the decision")

class LLMTradeAnalyzer:
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        self.output_parser = PydanticOutputParser(pydantic_object=TradingSignal)
        self.system_prompt = SWING_TRADER_PROMPT
        
    async def analyze(self, market_data: dict, technical_analysis: dict, price_action: List[dict]) -> TradingSignal:
        """Generate trading signal from market and technical data"""
        
        analysis_prompt = f"""
        Market Conditions:
        {market_data}
        
        Technical Analysis:
        {technical_analysis}
        
        Raw Price Data:
        {price_action}
        
        Based on this data, generate a trading decision in the required JSON format.
        {self.output_parser.get_format_instructions()}
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=analysis_prompt)
        ]

        print(messages)
        
        response = await self.llm.agenerate([messages])
        return self.output_parser.parse(response.generations[0][0].text)
    