from datetime import datetime
from typing import Dict, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository.zerodha_auth_repository import ZerodhaAuthRepository
from ..config.settings import settings

class ZerodhaAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_repo = ZerodhaAuthRepository()
        
    def get_login_url(self) -> str:
        """Get Zerodha login URL"""
        return self.auth_repo.get_login_url()
    
    async def handle_login_callback(self, request_token: str) -> Dict:
        """Handle login callback and token exchange"""
        try:
            # Exchange request token for access token
            auth_response = await self.auth_repo.exchange_token(request_token)
            
            if auth_response["status"] == "success":
                data = auth_response["data"]
                
                # Update settings with new tokens
                settings.ZERODHA_ACCESS_TOKEN = data["access_token"]
                
                # You might want to store these in a secure way
                # For now, just returning the response
                return {
                    "status": "success",
                    "access_token": data["access_token"],
                    "user_id": data["user_id"],
                    "login_time": data["login_time"]
                }
            else:
                raise Exception("Authentication failed")
                
        except Exception as e:
            logger.error(f"Error in login callback: {str(e)}")
            raise 