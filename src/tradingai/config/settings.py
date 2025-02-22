from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "TradingAI"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432  # Add port
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "tradingai"
    
    # Zerodha settings
    ZERODHA_API_KEY: str
    ZERODHA_API_SECRET: str
    ZERODHA_ACCESS_TOKEN: Optional[str] = None
    
    # Trading settings
    VALID_SYMBOLS: List[str] = [
        "RELIANCE", "TCS", "INFY", "HDFC", "ICICI",
        # Add more valid symbols
    ]
    
    # Mock settings
    USE_MOCK_ZERODHA: bool = False  # Set to False to use real API
    
    # API settings
    API_KEY: str = "your-secret-key"
    
    # LLM Settings
    LLM_MODEL_NAME: str = "gpt-4"
    OPENAI_API_KEY: str = "sk-..."
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 