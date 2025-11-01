"""
Twilio API client for VidyaVani IVR Learning System
"""

import logging
from typing import Dict, Optional, Any
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Record, Play
from config import Config

logger = logging.getLogger(__name__)

class TwilioClient:
    """Client for interacting with Twilio APIs"""
    
    def __init__(self):
        self.config = Config()
        self.account_sid = self.config.TWILIO_ACCOUNT_SID
        self.auth_token = self.config.TWILIO_AUTH_TOKEN
        self.phone_number = self.config.TWILIO_PHONE_NUMBER
        
        # Initialize Twilio client
        self.client = Client(self.account_sid, self.auth_token)
        
    def make_call(self, to_number: str, from_number: str = None, twiml_url: str = None) -> Dict[str, Any]:
        """
        Make an outbound call using Twilio
        
        Args:
            to_number: Destination phone number (E.164 format)
            from_number: Source phone number (defaults to configured number)
            twiml_url: URL that returns TwiML instructions
            
        Returns:
            Dict containing call details
        """
        if not from_number:
            from_number = self.phone_number
            
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=from_number,
                url=twiml_url or f"{self.config.BASE_URL}/webhook/incoming-call",
                method='POST'
            )
            
            logger.info(f"Call initiated successfully to {to_number}, SID: {call.sid}")
            return {
                'sid': call.sid,
                'status': call.status,
                'to': call.to,
                'from': call.from_,
                'direction': call.direction
            }
            
        except Exception as e:
            logger.error(f"Failed to make call to {to_number}: {str(e)}")
            raise
    
    def send_sms(self, to_number: str, message: str, from_number: str = None) -> Dict[str, Any]:
        """
        Send SMS using Twilio
        
        Args:
            to_number: Destination phone number (E.164 format)
            message: SMS message content
            from_number: Source phone number (defaults to configured number)
            
        Returns:
            Dict containing SMS details
        """
        if not from_number:
            from_number = self.phone_number
            
        try:
            sms = self.client.messages.create(
                to=to_number,
                from_=from_number,
                body=message
            )
            
            logger.info(f"SMS sent successfully to {to_number}, SID: {sms.sid}")
            return {
                'sid': sms.sid,
                'status': sms.status,
                'to': sms.to,
                'from': sms.from_,
                'body': sms.body
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
            raise
    
    def get_call_details(self, call_sid: str) -> Dict[str, Any]:
        """
        Get details of a specific call
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Dict containing call details
        """
        try:
            call = self.client.calls(call_sid).fetch()
            
            logger.info(f"Retrieved call details for {call_sid}")
            return {
                'sid': call.sid,
                'status': call.status,
                'duration': call.duration,
                'to': call.to,
                'from': call.from_,
                'direction': call.direction,
                'start_time': str(call.start_time),
                'end_time': str(call.end_time)
            }
            
        except Exception as e:
            logger.error(f"Failed to get call details for {call_sid}: {str(e)}")
            raise
    
    def get_account_details(self) -> Dict[str, Any]:
        """
        Get account details (without balance)
        
        Returns:
            Dict containing account information
        """
        try:
            account = self.client.api.accounts(self.account_sid).fetch()
            
            logger.info("Retrieved account details successfully")
            return {
                'account_sid': account.sid,
                'friendly_name': account.friendly_name,
                'status': account.status
            }
            
        except Exception as e:
            logger.error(f"Failed to get account details: {str(e)}")
            raise

    def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance
        
        Returns:
            Dict containing balance and currency
        """
        try:
            balance = self.client.balance.fetch()
            logger.info("Retrieved account balance successfully")
            return {
                'balance': balance.balance,
                'currency': balance.currency
            }
        except Exception as e:
            logger.error(f"Failed to get account balance: {str(e)}")
            raise
    
    def validate_connection(self) -> bool:
        """
        Validate Twilio API connection and credentials
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.get_account_details()
            logger.info("✅ Twilio connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Twilio connection validation failed: {str(e)}")
            return False
    
    @staticmethod
    def create_twiml_response() -> VoiceResponse:
        """
        Create a new TwiML VoiceResponse object
        
        Returns:
            VoiceResponse object for building TwiML
        """
        return VoiceResponse()
    
    @staticmethod
    def generate_gather_twiml(prompt: str, num_digits: int = 1, timeout: int = 5, 
                             action_url: str = None) -> str:
        """
        Generate TwiML for gathering DTMF input
        
        Args:
            prompt: Text to speak before gathering input
            num_digits: Number of digits to gather
            timeout: Timeout in seconds
            action_url: URL to POST the gathered digits
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        gather = Gather(num_digits=num_digits, timeout=timeout, action=action_url, method='POST')
        gather.say(prompt, voice='Polly.Aditi', language='en-IN')
        response.append(gather)
        
        # Fallback if no input
        response.say("We didn't receive any input. Goodbye!", voice='Polly.Aditi', language='en-IN')
        response.hangup()
        
        return str(response)
    
    @staticmethod
    def generate_record_twiml(prompt: str, max_length: int = 15, 
                             action_url: str = None, play_beep: bool = True) -> str:
        """
        Generate TwiML for recording audio
        
        Args:
            prompt: Text to speak before recording
            max_length: Maximum recording length in seconds
            action_url: URL to POST the recording URL
            play_beep: Whether to play a beep before recording
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        response.say(prompt, voice='Polly.Aditi', language='en-IN')
        response.record(
            max_length=max_length,
            action=action_url,
            method='POST',
            play_beep=play_beep,
            recording_status_callback=action_url,
            recording_status_callback_method='POST'
        )
        return str(response)
    
    @staticmethod
    def generate_play_twiml(audio_url: str, say_text: str = None) -> str:
        """
        Generate TwiML for playing audio
        
        Args:
            audio_url: URL of audio file to play
            say_text: Optional text to speak before playing audio
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        if say_text:
            response.say(say_text, voice='Polly.Aditi', language='en-IN')
        response.play(audio_url)
        return str(response)
    
    @staticmethod
    def generate_say_twiml(text: str, voice: str = 'Polly.Aditi', language: str = 'en-IN') -> str:
        """
        Generate TwiML for text-to-speech
        
        Args:
            text: Text to speak
            voice: Twilio voice to use
            language: Language code
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        response.say(text, voice=voice, language=language)
        return str(response)
    
    @staticmethod
    def generate_hangup_twiml(goodbye_message: str = "Thank you for using VidyaVani. Goodbye!") -> str:
        """
        Generate TwiML for hanging up
        
        Args:
            goodbye_message: Message to speak before hanging up
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        response.say(goodbye_message, voice='Polly.Aditi', language='en-IN')
        response.hangup()
        return str(response)

# Global instance
twilio_client = TwilioClient()
