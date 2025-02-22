# TradingAI 🤖 📈

An AI-powered trading analysis system that combines technical analysis with LLM-based decision making. The system analyzes market conditions, technical indicators, and uses GPT-4 to generate trading decisions.

## Overview 🌟

TradingAI helps traders by:
- Analyzing market conditions using EMA-based scoring
- Identifying stocks in Stage 2 uptrend
- Providing AI-powered trading decisions with entry/exit points
- Automating data collection and analysis

## Features

### Data Management 📊
- Historical data fetching from Zerodha
- Daily EOD data updates
- Data validation and cleaning
- Efficient PostgreSQL storage

### Technical Analysis 📈
- Moving Averages (SMA, EMA)
- MACD Indicator
- Bollinger Bands
- Volume Analysis
- Market Breadth

### AI Analysis 🧠
- Market Condition Assessment (6-point scoring)
- Pattern Recognition
- Trading Signal Generation
- Risk Assessment
- Stop Loss Calculation

### API Interface 🔌
- RESTful API endpoints
- Real-time analysis
- Historical data access
- Batch operations

## Installation 🚀

1. Clone the repository:

git clone https://github.com/mitesh-sharma/tradingai.git
cd tradingai

2. Create and activate virtual environment:
python -m venv venv
source venv/bin/activate 

3. Install dependencies:
pip install -e ".[dev]"

4. Set up environment variables:
cp .env.example .env

Edit .env with your credentials

5. Set up database:
createdb tradingai

## Configuration ⚙️

Required environment variables in `.env`:
Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=tradingai
API Security
API_KEY=your_api_key
Zerodha
ZERODHA_API_KEY=your_zerodha_api_key
ZERODHA_API_SECRET=your_zerodha_secret
ZERODHA_USER_ID=your_zerodha_user_id
OpenAI
OPENAI_API_KEY=your_openai_key
LLM_MODEL_NAME=gpt-4

## Usage 📡

1. Start the server:
uvicorn src.tradingai.main:app --reload

2. Fetch historical data:
curl -X POST http://localhost:8000/api/v1/stock/stocks/historical \
-H "Content-Type: application/json" \
-H "X-API-Key: your-secret-key" \
-d '{
"symbols": ["ZOTA"],
"from_date": "2023-02-22",
"to_date": "2024-02-22"
}'

3. Get analysis with LLM decision:
curl http://localhost:8000/api/v1/stock/analyze/ZOTA/with-decision \
-H "X-API-Key: your-secret-key"

## API Endpoints 🛣️
- `POST /api/v1/stock/stocks/historical`: Fetch historical data
- `GET /api/v1/stock/analyze/{symbol}`: Get technical analysis
- `GET /api/v1/stock/analyze/{symbol}/with-decision`: Get analysis with LLM trading decision
- `GET /api/v1/stock/symbols`: List all available symbols
- `POST /api/v1/stock/daily-update`: Trigger daily data update

## Technical Details 🔧

### Market Analysis
- Uses 6-point EMA scoring system
- Analyzes market breadth
- Provides market context and direction

### Stock Analysis
- 30-week SMA trend analysis
- MACD confirmation
- Bollinger Band correction opportunities
- Volume trend analysis

### LLM Integration
- Uses GPT-4 for decision making
- Structured prompts for consistent analysis
- Includes market context in decisions
- Provides detailed reasoning

## Contributing 🤝

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Author 👨‍💻

**Mitesh Sharma**
- GitHub: [@mitesh-sharma](https://github.com/mitesh-sharma)

## Acknowledgments 🙏

- [Zerodha](https://zerodha.com/) for their trading API
- [OpenAI](https://openai.com/) for GPT-4 API
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for database ORM
