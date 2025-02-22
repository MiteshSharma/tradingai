from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..repository.database import get_db
from ..service.zerodha_auth_service import ZerodhaAuthService

router = APIRouter(tags=["auth"])

@router.get("/auth/login")
async def login(
    db: AsyncSession = Depends(get_db)
):
    """Start Zerodha login flow by redirecting to Zerodha login page"""
    try:
        auth_service = ZerodhaAuthService(db)
        login_url = auth_service.get_login_url()
        
        # Redirect directly to Zerodha login page
        return RedirectResponse(url=login_url)
        
    except Exception as e:
        logger.error(f"Error initiating login: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auth/callback")
async def auth_callback(
    request_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle Zerodha login callback"""
    try:
        auth_service = ZerodhaAuthService(db)
        result = await auth_service.handle_login_callback(request_token)
        
        return result
    except Exception as e:
        logger.error(f"Error in auth callback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 