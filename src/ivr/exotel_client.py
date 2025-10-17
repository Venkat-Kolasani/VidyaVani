"""
Exotel API client for VidyaVani IVR Learning System
"""

import requests
import base64
import logging
from typing import Dict, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class ExotelClient:
    """Client for interacting with Exotel APIs"""
    
    def __init__(self):
        self.config = Config()
        self.base_url = f"https://api.exotel.com/v1/Accounts/{self.config.EXOTEL_ACCOUNT_SID}"
        
        # Create authentication header
        credentials = f"{self.config.EXOTEL_API_KEY}:{self.config.EXOTEL_API_TOKEN}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    def make_call(self, to_number: str, from_number: str = None, app_id: str = None) -> Dict[str, Any]:
        """
        Make an outbound call using Exotel
        
        Args:
            to_number: Destination phone number
            from_number: Source phone number (defaults to configured number)
            app_id: Exotel app ID (defaults to configured app ID)
            
        Returns:
            Dict containing call details
        """
        if not from_number:
            from_number = self.config.EXOTEL_PHONE_NUMBER
        if not app_id:
            app_id = self.config.EXOTEL_APP_ID
            
        url = f"{self.base_url}/Calls/connect.json"
        
        data = {
            'From': from_number,
            'To': to_number,
            'CallerId': from_number,
            'AppId': app_id
        }
        
        try:
            response = requests.post(url, headers=self.headers, data=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Call initiated successfully to {to_number}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to make call to {to_number}: {str(e)}")
            raise
    
    def send_sms(self, to_number: str, message: str, from_number: str = None) -> Dict[str, Any]:
        """
        Send SMS using Exotel
        
        Args:
            to_number: Destination phone number
            message: SMS message content
            from_number: Source phone number (defaults to configured number)
            
        Returns:
            Dict containing SMS details
        """
        if not from_number:
            from_number = self.config.EXOTEL_PHONE_NUMBER
            
        url = f"{self.base_url}/Sms/send.json"
        
        data = {
            'From': from_number,
            'To': to_number,
            'Body': message
        }
        
        try:
            response = requests.post(url, headers=self.headers, data=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"SMS sent successfully to {to_number}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
            raise
    
    def get_call_details(self, call_sid: str) -> Dict[str, Any]:
        """
        Get details of a specific call
        
        Args:
            call_sid: Exotel call SID
            
        Returns:
            Dict containing call details
        """
        url = f"{self.base_url}/Calls/{call_sid}.json"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Retrieved call details for {call_sid}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get call details for {call_sid}: {str(e)}")
            raise
    
    def get_account_details(self) -> Dict[str, Any]:
        """
        Get account details and balance
        
        Returns:
            Dict containing account information
        """
        url = f"{self.base_url}.json"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info("Retrieved account details successfully")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get account details: {str(e)}")
            raise
    
    def validate_connection(self) -> bool:
        """
        Validate Exotel API connection and credentials
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.get_account_details()
            logger.info("✅ Exotel connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Exotel connection validation failed: {str(e)}")
            return False

# Global instance
exotel_client = ExotelClient()