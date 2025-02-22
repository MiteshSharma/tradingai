import hashlib
import aiohttp
from typing import Dict, Optional
from loguru import logger

from ..config.settings import settings

class ZerodhaAuthRepository:
    def __init__(self):
        self.base_url = "https://api.kite.trade"
        self.login_url = "https://kite.zerodha.com/connect/login"
        self.api_key = "5e7n3q7ecslzkv0p"
        self.api_secret = "m7e0wgmuhi660mlpbxzcvc0u51sy0nqh"
        
    def get_login_url(self) -> str:
        """Get the Zerodha login URL"""
        return f"{self.login_url}?v=3&api_key={self.api_key}"
    
    def generate_checksum(self, request_token: str) -> str:
        """Generate SHA-256 checksum for token exchange"""
        # Log the values being used (remove in production)
        logger.debug(f"API Key: {self.api_key}")
        logger.debug(f"Request Token: {request_token}")
        logger.debug(f"API Secret: {self.api_secret}")
        
        raw = f"{self.api_key}{request_token}{self.api_secret}"
        checksum = hashlib.sha256(raw.encode()).hexdigest()
        
        logger.debug(f"Generated Checksum: {checksum}")
        return checksum
    
    async def exchange_token(self, request_token: str) -> Dict:
        """Exchange request token for access token"""
        try:
            checksum = self.generate_checksum(request_token)
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-Kite-Version": "3"
                }
                data = {
                    "api_key": self.api_key,
                    "request_token": request_token,
                    "checksum": checksum
                }
                
                logger.debug(f"Sending token exchange request with data: {data}")
                
                async with session.post(
                    f"{self.base_url}/session/token",
                    headers=headers,
                    data=data
                ) as response:
                    response_data = await response.json()
                    if response.status != 200:
                        logger.error(f"Token exchange failed. Response: {response_data}")
                        raise Exception(f"Token exchange failed: {response_data}")
                    
                    return response_data
                    
        except Exception as e:
            logger.error(f"Error exchanging token: {str(e)}")
            raise