from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import yaml
from pathlib import Path
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .config.settings import settings
from .api import health, stock, auth, instrument
from .repository.database import init_models
from .repository.instrument_repository import InstrumentRepository
from .service.instrument_service import InstrumentService
from .repository.zerodha import ZerodhaClient
from .service.stock_service import StockService

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        openapi_url="/openapi.json",  # Explicitly set OpenAPI URL
        docs_url="/docs"  # Explicitly set Swagger UI URL
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add routers
    app.include_router(health.router, prefix=settings.API_V1_PREFIX)
    app.include_router(stock.router, prefix=settings.API_V1_PREFIX)
    app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
    app.include_router(instrument.router, prefix=settings.API_V1_PREFIX)

    @app.on_event("startup")
    async def startup_event():
        logger.info("Initializing database...")
        await init_models()
        logger.info(f"Application {settings.APP_NAME} initialized")

    def custom_openapi():
        """Load OpenAPI spec from yaml file"""
        try:
            if app.openapi_schema:
                return app.openapi_schema

            # Get the directory of the current file
            current_dir = Path(__file__).parent.parent.parent
            swagger_file = current_dir / "docs" / "openapi" / "swagger.yaml"
            
            logger.info(f"Loading OpenAPI spec from {swagger_file}")
            
            if swagger_file.exists():
                with swagger_file.open() as f:
                    app.openapi_schema = yaml.safe_load(f)
                logger.info("Successfully loaded OpenAPI spec from file")
            else:
                logger.warning(f"Swagger file not found at {swagger_file}, using auto-generated schema")
                # Fallback to auto-generated schema
                app.openapi_schema = get_openapi(
                    title=settings.APP_NAME,
                    version="1.0.0",
                    description="TradingAI API",
                    routes=app.routes,
                )
            return app.openapi_schema
        except Exception as e:
            logger.error(f"Error loading OpenAPI spec: {str(e)}")
            # Fallback to auto-generated schema
            return get_openapi(
                title=settings.APP_NAME,
                version="1.0.0",
                description="TradingAI API",
                routes=app.routes,
            )

    app.openapi = custom_openapi
    return app

app = create_app()

async def setup_services(db: AsyncSession):
    instrument_repo = InstrumentRepository()
    instrument_service = InstrumentService(db, instrument_repo)
    zerodha_client = ZerodhaClient(instrument_service)
    stock_service = StockService(db, zerodha_client, instrument_service)
    return stock_service 