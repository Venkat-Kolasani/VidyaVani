"""
IVR Handler for VidyaVani Learning System
Handles Exotel webhook endpoints and XML response generation
"""

import logging
from typing import Dict, Any, Optional
from flask import request, Response
from datetime import datetime
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class IVRHandler:
    """Handles IVR call flows and XML response generation"""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        
        # Menu states
        self.MENU_STATES = {
            'welcome': 'welcome',
            'language_selection': 'language_selection',
            'grade_confirmation': 'grade_confirmation',
            'interaction_mode': 'interaction_mode',
            'recording_question': 'recording_question',
            'processing_question': 'processing_question',
            'delivering_response': 'delivering_response',
            'follow_up_menu': 'follow_up_menu'
        }
        
        # Language mappings
        self.LANGUAGES = {
            '1': 'english',
            '2': 'telugu'
        }
        
        # Menu option mappings
        self.MENU_OPTIONS = {
            '1': 'detailed_explanation',
            '2': 'repeat_answer',
            '3': 'new_question',
            '9': 'main_menu'
        }
    
    def handle_incoming_call(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle incoming call webhook from Exotel
        
        Args:
            request_data: Webhook payload from Exotel
            
        Returns:
            XML response for Exotel
        """
        try:
            # Extract call information
            call_sid = request_data.get('CallSid', '')
            from_number = request_data.get('From', '')
            to_number = request_data.get('To', '')
            
            logger.info(f"Incoming call from {from_number} to {to_number}, CallSid: {call_sid}")
            
            # Create or get session
            session = self.session_manager.create_session(from_number)
            session.call_sid = call_sid
            session.call_active = True
            
            # Update session menu state
            self.session_manager.update_session_menu(from_number, self.MENU_STATES['welcome'])
            
            # Generate welcome XML response
            xml_response = self._generate_welcome_xml()
            
            logger.info(f"Generated welcome response for {from_number}")
            return Response(xml_response, mimetype='application/xml')
            
        except Exception as e:
            logger.error(f"Error handling incoming call: {str(e)}")
            return self._generate_error_xml("Sorry, there was a technical issue. Please try calling again.")
    
    def handle_language_selection(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle language selection via DTMF
        
        Args:
            request_data: Webhook payload with DTMF digits
            
        Returns:
            XML response for grade confirmation
        """
        try:
            from_number = request_data.get('From', '')
            digits = request_data.get('Digits', '')
            
            logger.info(f"Language selection from {from_number}: {digits}")
            
            # Validate language selection
            if digits not in self.LANGUAGES:
                logger.warning(f"Invalid language selection: {digits}")
                return self._generate_invalid_selection_xml("language")
            
            # Update session language
            language = self.LANGUAGES[digits]
            success = self.session_manager.update_session_language(from_number, language)
            
            if not success:
                logger.error(f"Failed to update language for {from_number}")
                return self._generate_error_xml("Session error. Please try calling again.")
            
            # Update menu state
            self.session_manager.update_session_menu(from_number, self.MENU_STATES['grade_confirmation'])
            
            # Generate grade confirmation XML
            xml_response = self._generate_grade_confirmation_xml(language)
            
            logger.info(f"Language set to {language} for {from_number}")
            return Response(xml_response, mimetype='application/xml')
            
        except Exception as e:
            logger.error(f"Error handling language selection: {str(e)}")
            return self._generate_error_xml("Sorry, there was an error. Please try again.")
    
    def handle_grade_confirmation(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle grade confirmation and proceed to interaction mode
        
        Args:
            request_data: Webhook payload
            
        Returns:
            XML response for interaction mode selection
        """
        try:
            from_number = request_data.get('From', '')
            
            # Get session to determine language
            session = self.session_manager.get_session(from_number)
            if not session:
                return self._generate_error_xml("Session not found. Please call again.")
            
            # Update menu state
            self.session_manager.update_session_menu(from_number, self.MENU_STATES['interaction_mode'])
            
            # Generate interaction mode XML
            xml_response = self._generate_interaction_mode_xml(session.language)
            
            logger.info(f"Grade confirmed for {from_number}, language: {session.language}")
            return Response(xml_response, mimetype='application/xml')
            
        except Exception as e:
            logger.error(f"Error handling grade confirmation: {str(e)}")
            return self._generate_error_xml("Sorry, there was an error. Please try again.")
    
    def handle_interaction_mode_selection(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle interaction mode selection (ask question directly)
        
        Args:
            request_data: Webhook payload with DTMF digits
            
        Returns:
            XML response to start question recording
        """
        try:
            from_number = request_data.get('From', '')
            digits = request_data.get('Digits', '')
            
            # Get session
            session = self.session_manager.get_session(from_number)
            if not session:
                return self._generate_error_xml("Session not found. Please call again.")
            
            logger.info(f"Interaction mode selection from {from_number}: {digits}")
            
            # For now, only support direct question asking (option 2)
            if digits == '2':
                # Update menu state
                self.session_manager.update_session_menu(from_number, self.MENU_STATES['recording_question'])
                
                # Generate question recording XML
                xml_response = self._generate_question_recording_xml(session.language)
                
                logger.info(f"Starting question recording for {from_number}")
                return Response(xml_response, mimetype='application/xml')
            
            elif digits == '1':
                # Topic browsing not implemented yet
                xml_response = self._generate_feature_not_available_xml(session.language, "topic browsing")
                return Response(xml_response, mimetype='application/xml')
            
            else:
                logger.warning(f"Invalid interaction mode selection: {digits}")
                return self._generate_invalid_selection_xml("interaction", session.language)
                
        except Exception as e:
            logger.error(f"Error handling interaction mode selection: {str(e)}")
            return self._generate_error_xml("Sorry, there was an error. Please try again.")
    
    def handle_question_recording(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle recorded question from user
        
        Args:
            request_data: Webhook payload with recording URL
            
        Returns:
            XML response indicating processing
        """
        try:
            from_number = request_data.get('From', '')
            recording_url = request_data.get('RecordingUrl', '')
            recording_duration = request_data.get('RecordingDuration', '0')
            
            # Get session
            session = self.session_manager.get_session(from_number)
            if not session:
                return self._generate_error_xml("Session not found. Please call again.")
            
            logger.info(f"Question recorded from {from_number}: {recording_url}, duration: {recording_duration}s")
            
            # Store recording info in session (for processing pipeline)
            session.current_recording_url = recording_url
            session.current_recording_duration = float(recording_duration)
            
            # Update menu state
            self.session_manager.update_session_menu(from_number, self.MENU_STATES['processing_question'])
            
            # Generate processing message XML
            xml_response = self._generate_processing_xml(session.language)
            
            logger.info(f"Processing question for {from_number}")
            return Response(xml_response, mimetype='application/xml')
            
        except Exception as e:
            logger.error(f"Error handling question recording: {str(e)}")
            return self._generate_error_xml("Sorry, there was an error processing your question.")
    
    def handle_response_delivery(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle delivery of AI-generated response
        
        Args:
            request_data: Webhook payload with response audio URL
            
        Returns:
            XML response with follow-up menu
        """
        try:
            from_number = request_data.get('From', '')
            response_audio_url = request_data.get('ResponseAudioUrl', '')
            
            # Get session
            session = self.session_manager.get_session(from_number)
            if not session:
                return self._generate_error_xml("Session not found. Please call again.")
            
            logger.info(f"Delivering response to {from_number}: {response_audio_url}")
            
            # Update menu state
            self.session_manager.update_session_menu(from_number, self.MENU_STATES['follow_up_menu'])
            
            # Generate response delivery with follow-up menu XML
            xml_response = self._generate_response_delivery_xml(response_audio_url, session.language)
            
            logger.info(f"Response delivered to {from_number}")
            return Response(xml_response, mimetype='application/xml')
            
        except Exception as e:
            logger.error(f"Error handling response delivery: {str(e)}")
            return self._generate_error_xml("Sorry, there was an error delivering the response.")
    
    def handle_follow_up_menu(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle follow-up menu selection after response delivery
        
        Args:
            request_data: Webhook payload with DTMF digits
            
        Returns:
            XML response based on menu selection
        """
        try:
            from_number = request_data.get('From', '')
            digits = request_data.get('Digits', '')
            
            # Get session
            session = self.session_manager.get_session(from_number)
            if not session:
                return self._generate_error_xml("Session not found. Please call again.")
            
            logger.info(f"Follow-up menu selection from {from_number}: {digits}")
            
            if digits == '1':  # Detailed explanation
                # TODO: Implement detailed explanation logic
                xml_response = self._generate_feature_not_available_xml(session.language, "detailed explanation")
                return Response(xml_response, mimetype='application/xml')
            
            elif digits == '2':  # Repeat answer
                # TODO: Implement repeat answer logic
                xml_response = self._generate_feature_not_available_xml(session.language, "repeat answer")
                return Response(xml_response, mimetype='application/xml')
            
            elif digits == '3':  # New question
                # Reset to question recording
                self.session_manager.update_session_menu(from_number, self.MENU_STATES['recording_question'])
                xml_response = self._generate_question_recording_xml(session.language)
                return Response(xml_response, mimetype='application/xml')
            
            elif digits == '9':  # Main menu
                # Reset to interaction mode
                self.session_manager.update_session_menu(from_number, self.MENU_STATES['interaction_mode'])
                xml_response = self._generate_interaction_mode_xml(session.language)
                return Response(xml_response, mimetype='application/xml')
            
            else:
                logger.warning(f"Invalid follow-up menu selection: {digits}")
                return self._generate_invalid_selection_xml("follow_up", session.language)
                
        except Exception as e:
            logger.error(f"Error handling follow-up menu: {str(e)}")
            return self._generate_error_xml("Sorry, there was an error. Please try again.")
    
    def handle_call_end(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle call end webhook
        
        Args:
            request_data: Webhook payload
            
        Returns:
            Empty response (call already ended)
        """
        try:
            from_number = request_data.get('From', '')
            call_sid = request_data.get('CallSid', '')
            
            logger.info(f"Call ended: {from_number}, CallSid: {call_sid}")
            
            # End session
            self.session_manager.end_session(from_number)
            
            return Response('', mimetype='application/xml')
            
        except Exception as e:
            logger.error(f"Error handling call end: {str(e)}")
            return Response('', mimetype='application/xml')
    
    # XML Generation Methods
    
    def _generate_welcome_xml(self) -> str:
        """Generate welcome message XML"""
        root = ET.Element('Response')
        
        # Welcome message
        say = ET.SubElement(root, 'Say', voice='alice', language='en-IN')
        say.text = "Welcome to VidyaVani, your AI learning assistant. Press 1 for English or Press 2 for Telugu."
        
        # Gather DTMF input for language selection
        gather = ET.SubElement(root, 'Gather', 
                              numDigits='1', 
                              timeout='10',
                              action='/webhook/language-selection',
                              method='POST')
        
        # Repeat instructions in gather
        say_gather = ET.SubElement(gather, 'Say', voice='alice', language='en-IN')
        say_gather.text = "Press 1 for English or Press 2 for Telugu."
        
        # Fallback if no input
        say_fallback = ET.SubElement(root, 'Say', voice='alice', language='en-IN')
        say_fallback.text = "No input received. Goodbye."
        
        hangup = ET.SubElement(root, 'Hangup')
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_grade_confirmation_xml(self, language: str) -> str:
        """Generate grade confirmation XML"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "Great! You have selected English. This system helps Class 10 students with Science questions. Press any key to continue."
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'  # Using English voice for now, can be enhanced later
            message = "మీరు తెలుగు ఎంచుకున్నారు. ఈ సిస్టమ్ క్లాస్ 10 విద్యార్థులకు సైన్స్ ప్రశ్నలతో సహాయం చేస్తుంది. కొనసాగించడానికి ఏదైనా కీ నొక్కండి."
        
        # Grade confirmation message
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Gather any key to continue
        gather = ET.SubElement(root, 'Gather',
                              numDigits='1',
                              timeout='10',
                              action='/webhook/grade-confirmation',
                              method='POST')
        
        # Redirect to interaction mode after any key press
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/interaction-mode'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_interaction_mode_xml(self, language: str) -> str:
        """Generate interaction mode selection XML"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "How would you like to learn today? Press 1 to browse topics or Press 2 to ask a question directly."
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'
            message = "ఈరోజు మీరు ఎలా నేర్చుకోవాలనుకుంటున్నారు? టాపిక్స్ బ్రౌజ్ చేయడానికి 1 నొక్కండి లేదా నేరుగా ప్రశ్న అడగడానికి 2 నొక్కండి."
        
        # Interaction mode message
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Gather DTMF input
        gather = ET.SubElement(root, 'Gather',
                              numDigits='1',
                              timeout='15',
                              action='/webhook/interaction-mode-selection',
                              method='POST')
        
        # Repeat instructions in gather
        say_gather = ET.SubElement(gather, 'Say', voice=voice, language=lang)
        say_gather.text = "Press 1 to browse topics or Press 2 to ask a question."
        
        # Fallback
        say_fallback = ET.SubElement(root, 'Say', voice=voice, language=lang)
        if language == 'english':
            say_fallback.text = "No input received. Goodbye."
        else:
            say_fallback.text = "ఇన్‌పుట్ రాలేదు. వీడ్కోలు."
        
        hangup = ET.SubElement(root, 'Hangup')
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_question_recording_xml(self, language: str) -> str:
        """Generate question recording XML"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "Please ask your science question clearly. You have 15 seconds. Start speaking after the beep."
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'
            message = "దయచేసి మీ సైన్స్ ప్రశ్నను స్పష్టంగా అడగండి. మీకు 15 సెకన్లు ఉన్నాయి. బీప్ తర్వాత మాట్లాడటం ప్రారంభించండి."
        
        # Recording instruction
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Record the question
        record = ET.SubElement(root, 'Record',
                              maxLength='15',
                              timeout='3',
                              finishOnKey='#',
                              action='/webhook/question-recording',
                              method='POST',
                              recordingStatusCallback='/webhook/recording-status')
        
        # Fallback message
        say_fallback = ET.SubElement(root, 'Say', voice=voice, language=lang)
        if language == 'english':
            say_fallback.text = "Recording completed. Processing your question."
        else:
            say_fallback.text = "రికార్డింగ్ పూర్తయింది. మీ ప్రశ్నను ప్రాసెస్ చేస్తున్నాము."
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_processing_xml(self, language: str) -> str:
        """Generate processing message XML"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "Thank you for your question. I am processing it now. Please wait a moment."
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'
            message = "మీ ప్రశ్నకు ధన్యవాదాలు. నేను దానిని ఇప్పుడు ప్రాసెస్ చేస్తున్నాను. దయచేసి కాసేపు వేచి ఉండండి."
        
        # Processing message
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Pause for processing (this will be replaced by actual processing pipeline)
        pause = ET.SubElement(root, 'Pause', length='3')
        
        # Redirect to response delivery (will be handled by processing pipeline)
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/response-delivery'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_response_delivery_xml(self, response_audio_url: str, language: str) -> str:
        """Generate response delivery XML with follow-up menu"""
        root = ET.Element('Response')
        
        # Play the AI-generated response
        if response_audio_url:
            play = ET.SubElement(root, 'Play')
            play.text = response_audio_url
        else:
            # Fallback text response
            say = ET.SubElement(root, 'Say', voice='alice', language='en-IN')
            if language == 'english':
                say.text = "I apologize, but I couldn't generate an audio response. Please try asking your question again."
            else:
                say.text = "క్షమించండి, నేను ఆడియో రెస్పాన్స్ జనరేట్ చేయలేకపోయాను. దయచేసి మీ ప్రశ్నను మళ్లీ అడగండి."
        
        # Follow-up menu
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            menu_message = "Press 1 for detailed explanation, Press 2 to hear again, Press 3 for new question, or Press 9 for main menu."
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'
            menu_message = "వివరణ కోసం 1 నొక్కండి, మళ్లీ వినడానికి 2 నొక్కండి, కొత్త ప్రశ్న కోసం 3 నొక్కండి, లేదా మెయిన్ మెనూ కోసం 9 నొక్కండి."
        
        # Gather follow-up input
        gather = ET.SubElement(root, 'Gather',
                              numDigits='1',
                              timeout='15',
                              action='/webhook/follow-up-menu',
                              method='POST')
        
        say_gather = ET.SubElement(gather, 'Say', voice=voice, language=lang)
        say_gather.text = menu_message
        
        # Fallback
        say_fallback = ET.SubElement(root, 'Say', voice=voice, language=lang)
        if language == 'english':
            say_fallback.text = "Thank you for using VidyaVani. Goodbye!"
        else:
            say_fallback.text = "విద్యావాణిని ఉపయోగించినందుకు ధన్యవాదాలు. వీడ్కోలు!"
        
        hangup = ET.SubElement(root, 'Hangup')
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_invalid_selection_xml(self, menu_type: str, language: str = 'english') -> str:
        """Generate invalid selection XML"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            if menu_type == 'language':
                message = "Invalid selection. Press 1 for English or Press 2 for Telugu."
                action = '/webhook/language-selection'
            elif menu_type == 'interaction':
                message = "Invalid selection. Press 1 to browse topics or Press 2 to ask a question."
                action = '/webhook/interaction-mode-selection'
            elif menu_type == 'follow_up':
                message = "Invalid selection. Press 1 for detailed explanation, 2 to hear again, 3 for new question, or 9 for main menu."
                action = '/webhook/follow-up-menu'
            else:
                message = "Invalid selection. Please try again."
                action = '/webhook/main-menu'
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'
            if menu_type == 'language':
                message = "తప్పు ఎంపిక. ఇంగ్లీష్ కోసం 1 లేదా తెలుగు కోసం 2 నొక్కండి."
                action = '/webhook/language-selection'
            elif menu_type == 'interaction':
                message = "తప్పు ఎంపిక. టాపిక్స్ బ్రౌజ్ చేయడానికి 1 లేదా ప్రశ్న అడగడానికి 2 నొక్కండి."
                action = '/webhook/interaction-mode-selection'
            elif menu_type == 'follow_up':
                message = "తప్పు ఎంపిక. వివరణ కోసం 1, మళ్లీ వినడానికి 2, కొత్త ప్రశ్న కోసం 3, లేదా మెయిన్ మెనూ కోసం 9 నొక్కండి."
                action = '/webhook/follow-up-menu'
            else:
                message = "తప్పు ఎంపిక. దయచేసి మళ్లీ ప్రయత్నించండి."
                action = '/webhook/main-menu'
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Gather input again
        gather = ET.SubElement(root, 'Gather',
                              numDigits='1',
                              timeout='10',
                              action=action,
                              method='POST')
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_feature_not_available_xml(self, language: str, feature_name: str) -> str:
        """Generate feature not available XML"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = f"Sorry, {feature_name} is not available yet. Returning to main menu."
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'
            message = f"క్షమించండి, {feature_name} ఇంకా అందుబాటులో లేదు. మెయిన్ మెనూకు తిరిగి వెళ్తున్నాము."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Redirect to interaction mode
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/interaction-mode'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_error_xml(self, error_message: str) -> str:
        """Generate error XML response"""
        root = ET.Element('Response')
        
        say = ET.SubElement(root, 'Say', voice='alice', language='en-IN')
        say.text = error_message
        
        hangup = ET.SubElement(root, 'Hangup')
        
        return ET.tostring(root, encoding='unicode')