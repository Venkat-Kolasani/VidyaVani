"""
Error Recovery Handler for IVR System

This module handles error recovery flows and provides appropriate XML responses
for different error scenarios in the IVR system.
"""

import logging
from typing import Dict, Any, Optional
from flask import Response
import xml.etree.ElementTree as ET

from src.utils.error_handler import ErrorType, ErrorResponseTemplates
from src.utils.error_tracker import error_tracker

logger = logging.getLogger(__name__)


class IVRErrorRecoveryHandler:
    """Handles error recovery flows for IVR system"""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.error_templates = ErrorResponseTemplates()
    
    def handle_error_recovery(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle error recovery menu selections
        
        Args:
            request_data: Webhook payload with DTMF digits
            
        Returns:
            XML response based on recovery selection
        """
        from_number = request_data.get('From', 'unknown')
        digits = request_data.get('Digits', '')
        
        try:
            # Get session to determine language
            session = self.session_manager.get_session(from_number)
            language = session.language if session else 'english'
            
            logger.info(f"Error recovery selection from {from_number}: {digits}")
            
            if digits == '1':  # Try again
                # Reset session state and redirect to question recording
                if session:
                    self.session_manager.update_processing_status(from_number, 'ready')
                    self.session_manager.update_session_menu(from_number, 'recording_question')
                
                xml_response = self._generate_try_again_xml(language)
                return Response(xml_response, mimetype='application/xml')
            
            elif digits == '9':  # Main menu
                # Reset session and go to main menu
                if session:
                    self.session_manager.update_processing_status(from_number, 'ready')
                    self.session_manager.update_session_menu(from_number, 'interaction_mode')
                
                xml_response = self._generate_main_menu_redirect_xml(language)
                return Response(xml_response, mimetype='application/xml')
            
            else:
                # Invalid selection, show error recovery menu again
                xml_response = self._generate_invalid_recovery_selection_xml(language)
                return Response(xml_response, mimetype='application/xml')
                
        except Exception as e:
            logger.error(f"Error in error recovery handler: {e}")
            error_tracker.track_error(
                component='IVR_ErrorRecovery',
                error=e,
                phone_number=from_number,
                recovery_action='Fallback to system error message'
            )
            
            # Fallback to basic error message
            xml_response = self._generate_system_error_xml('english')
            return Response(xml_response, mimetype='application/xml')
    
    def _generate_try_again_xml(self, language: str) -> str:
        """Generate XML for trying again"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "Let's try again. Please ask your science question clearly after the beep."
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'
            message = "మళ్లీ ప్రయత్నిద్దాం. దయచేసి బీప్ తర్వాత మీ సైన్స్ ప్రశ్నను స్పష్టంగా అడగండి."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Record the question
        record = ET.SubElement(root, 'Record',
                              maxLength='15',
                              timeout='3',
                              finishOnKey='#',
                              action='/webhook/question-recording',
                              method='POST')
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_main_menu_redirect_xml(self, language: str) -> str:
        """Generate XML for main menu redirect"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "Returning to main menu."
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'
            message = "మెయిన్ మెనూకు తిరిగి వెళ్తున్నాము."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Redirect to interaction mode
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/interaction-mode'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_invalid_recovery_selection_xml(self, language: str) -> str:
        """Generate XML for invalid recovery selection"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "Invalid selection. Press 1 to try asking your question again, or Press 9 for main menu."
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'
            message = "తప్పు ఎంపిక. మీ ప్రశ్నను మళ్లీ అడగడానికి 1 నొక్కండి లేదా మెయిన్ మెనూ కోసం 9 నొక్కండి."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Gather input again
        gather = ET.SubElement(root, 'Gather',
                              numDigits='1',
                              timeout='10',
                              action='/webhook/error-recovery',
                              method='POST')
        
        # Fallback to main menu
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/interaction-mode'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_system_error_xml(self, language: str) -> str:
        """Generate XML for system errors"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "I'm experiencing technical difficulties. Please call back in a few minutes. Thank you for using VidyaVani."
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'
            message = "నాకు సాంకేతిక సమస్యలు ఉన్నాయి. దయచేసి కొన్ని నిమిషాల తర్వాత మళ్లీ కాల్ చేయండి. విద్యావాణిని ఉపయోగించినందుకు ధన్యవాదాలు."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        hangup = ET.SubElement(root, 'Hangup')
        
        return ET.tostring(root, encoding='unicode')
    
    def generate_graceful_fallback_xml(self, error_type: ErrorType, language: str, 
                                     context: Dict[str, Any] = None) -> str:
        """
        Generate graceful fallback XML for specific error types
        
        Args:
            error_type: Type of error that occurred
            language: User's language preference
            context: Additional context for the error
            
        Returns:
            XML response string
        """
        root = ET.Element('Response')
        
        # Get appropriate error message
        error_message = self.error_templates.get_message(error_type, language)
        
        voice = 'alice'
        lang = 'en-IN'
        
        # Main error message
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = error_message
        
        # Add recovery options based on error type
        response_template = self.error_templates.get_response(error_type)
        
        if response_template.retry_allowed:
            # Offer retry option
            if language == 'english':
                retry_message = "Press 1 to try again, or Press 9 for main menu."
            else:
                retry_message = "మళ్లీ ప్రయత్నించడానికి 1 నొక్కండి లేదా మెయిన్ మెనూ కోసం 9 నొక్కండి."
            
            gather = ET.SubElement(root, 'Gather',
                                  numDigits='1',
                                  timeout='10',
                                  action='/webhook/error-recovery',
                                  method='POST')
            
            say_gather = ET.SubElement(gather, 'Say', voice=voice, language=lang)
            say_gather.text = retry_message
        
        if response_template.redirect_to_menu:
            # Redirect to main menu after a pause
            pause = ET.SubElement(root, 'Pause', length='2')
            redirect = ET.SubElement(root, 'Redirect', method='POST')
            redirect.text = '/webhook/interaction-mode'
        else:
            # End call gracefully
            if language == 'english':
                goodbye_message = "Thank you for using VidyaVani. Goodbye!"
            else:
                goodbye_message = "విద్యావాణిని ఉపయోగించినందుకు ధన్యవాదాలు. వీడ్కోలు!"
            
            say_goodbye = ET.SubElement(root, 'Say', voice=voice, language=lang)
            say_goodbye.text = goodbye_message
            
            hangup = ET.SubElement(root, 'Hangup')
        
        return ET.tostring(root, encoding='unicode')
    
    def log_error_for_debugging(self, error_type: ErrorType, phone_number: str, 
                               context: Dict[str, Any] = None):
        """
        Log error information for debugging without exposing sensitive data
        
        Args:
            error_type: Type of error
            phone_number: Phone number (will be hashed)
            context: Additional context for debugging
        """
        import hashlib
        
        # Hash phone number for privacy
        phone_hash = hashlib.sha256(phone_number.encode()).hexdigest()[:8]
        
        debug_info = {
            'error_type': error_type.value,
            'phone_hash': phone_hash,
            'timestamp': logger.handlers[0].formatter.formatTime(logger.makeRecord(
                logger.name, logging.INFO, __file__, 0, "", (), None
            )) if logger.handlers else 'unknown',
            'context_summary': {
                'session_exists': context.get('session_exists', False) if context else False,
                'processing_stage': context.get('processing_stage', 'unknown') if context else 'unknown',
                'language': context.get('language', 'unknown') if context else 'unknown'
            } if context else {}
        }
        
        logger.info(f"Error logged for debugging: {debug_info}")
        
        # Store in error tracker for analysis
        error_tracker.track_error(
            component='IVR_ErrorRecovery_Debug',
            error=Exception(f"Error type: {error_type.value}"),
            phone_number=phone_number,
            recovery_action='Logged for debugging analysis'
        )