"""
IVR Handler for VidyaVani Learning System
Handles Exotel webhook endpoints and XML response generation
"""

import logging
from typing import Dict, Any, Optional
from flask import request, Response
from datetime import datetime
import xml.etree.ElementTree as ET
import threading
import time

from src.session.session_manager import ResponseData
from src.ivr.processing_pipeline import IVRProcessingPipeline
from src.ivr.error_recovery_handler import IVRErrorRecoveryHandler
from src.utils.error_handler import error_handler, ErrorType, with_retry, RetryConfig
from src.utils.error_tracker import error_tracker
from src.utils.call_recorder import call_recorder
from config import Config

logger = logging.getLogger(__name__)

class IVRHandler:
    """Handles IVR call flows and XML response generation"""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.config = Config()
        self.processing_pipeline = IVRProcessingPipeline(self.config)
        self.error_recovery_handler = IVRErrorRecoveryHandler(session_manager)
        
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
        Handle incoming call webhook from Exotel with enhanced error handling
        
        Args:
            request_data: Webhook payload from Exotel
            
        Returns:
            XML response for Exotel
        """
        from_number = request_data.get('From', 'unknown')
        
        try:
            # Extract call information
            call_sid = request_data.get('CallSid', '')
            to_number = request_data.get('To', '')
            
            logger.info(f"Incoming call from {from_number} to {to_number}, CallSid: {call_sid}")
            
            # Create or get session with error handling
            session = self.session_manager.create_session(from_number)
            if not session:
                raise Exception("Failed to create session")
                
            session.call_sid = call_sid
            session.call_active = True
            
            # Start call recording for demo purposes
            try:
                recording_id = call_recorder.start_recording(
                    phone_number=from_number,
                    session_id=session.session_id,
                    language='english',  # Default, will be updated when language is selected
                    demo_mode=True  # All calls are recorded as demo for presentation
                )
                logger.info(f"Started call recording {recording_id} for {from_number}")
            except Exception as recording_error:
                logger.warning(f"Failed to start call recording: {recording_error}")
            
            # Update session menu state
            self.session_manager.update_session_menu(from_number, self.MENU_STATES['welcome'])
            
            # Generate welcome XML response
            xml_response = self._generate_welcome_xml()
            
            logger.info(f"Generated welcome response for {from_number}")
            return Response(xml_response, mimetype='application/xml')
            
        except Exception as e:
            # Handle error with enhanced error handling
            error_response = error_handler.handle_error(
                error=e,
                component='IVR_IncomingCall',
                phone_number=from_number,
                language='english'  # Default to English for initial call
            )
            
            logger.error(f"Error handling incoming call from {from_number}: {error_response}")
            return self._generate_error_xml(error_response['message'])
    
    def handle_language_selection(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle language selection via DTMF with enhanced error handling
        
        Args:
            request_data: Webhook payload with DTMF digits
            
        Returns:
            XML response for grade confirmation
        """
        from_number = request_data.get('From', 'unknown')
        digits = request_data.get('Digits', '')
        
        try:
            logger.info(f"Language selection from {from_number}: {digits}")
            
            # Validate language selection
            if digits not in self.LANGUAGES:
                logger.warning(f"Invalid language selection: {digits} from {from_number}")
                # Use appropriate language for error message
                language = 'english'  # Default fallback
                error_response = error_handler.get_fallback_response(
                    ErrorType.INVALID_INPUT, language
                )
                return self._generate_invalid_selection_xml("language", language)
            
            # Update session language
            language = self.LANGUAGES[digits]
            success = self.session_manager.update_session_language(from_number, language)
            
            if not success:
                logger.error(f"Failed to update language for {from_number}")
                error_response = error_handler.get_fallback_response(
                    ErrorType.SYSTEM_ERROR, language
                )
                return self._generate_error_xml(error_response['message'])
            
            # Update recording language
            try:
                active_recording = call_recorder.get_active_recording(from_number)
                if active_recording:
                    active_recording.language = language
                    logger.debug(f"Updated recording language to {language} for {from_number}")
            except Exception as recording_error:
                logger.warning(f"Failed to update recording language: {recording_error}")
            
            # Update menu state
            self.session_manager.update_session_menu(from_number, self.MENU_STATES['grade_confirmation'])
            
            # Generate grade confirmation XML
            xml_response = self._generate_grade_confirmation_xml(language)
            
            logger.info(f"Language set to {language} for {from_number}")
            return Response(xml_response, mimetype='application/xml')
            
        except Exception as e:
            # Handle error with context
            error_response = error_handler.handle_error(
                error=e,
                component='IVR_LanguageSelection',
                phone_number=from_number,
                language='english'  # Default since language selection failed
            )
            
            return self._generate_error_xml(error_response['message'])
    
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
        Handle recorded question from user with enhanced validation and error handling
        
        Args:
            request_data: Webhook payload with recording URL
            
        Returns:
            XML response indicating processing or error
        """
        from_number = request_data.get('From', 'unknown')
        
        try:
            recording_url = request_data.get('RecordingUrl', '')
            recording_duration = request_data.get('RecordingDuration', '0')
            
            # Get session with error handling
            session = self.session_manager.get_session(from_number)
            if not session:
                error_response = error_handler.get_fallback_response(
                    ErrorType.SYSTEM_ERROR, 'english'
                )
                return self._generate_error_xml(error_response['message'])
            
            logger.info(f"Question recorded from {from_number}: {recording_url}, duration: {recording_duration}s")
            
            # Validate recording with enhanced error handling
            try:
                duration = float(recording_duration) if recording_duration else 0
            except (ValueError, TypeError):
                logger.error(f"Invalid recording duration for {from_number}: {recording_duration}")
                error_response = error_handler.get_fallback_response(
                    ErrorType.RECORDING_ISSUE, session.language
                )
                return self._generate_recording_failed_xml(session.language)
            
            # Check recording duration
            if duration < 1.0:  # Too short
                logger.warning(f"Recording too short for {from_number}: {duration}s")
                error_response = error_handler.get_fallback_response(
                    ErrorType.RECORDING_ISSUE, session.language
                )
                return self._generate_recording_too_short_xml(session.language)
            
            if duration > 16.0:  # Too long
                logger.warning(f"Recording too long for {from_number}: {duration}s")
                error_response = error_handler.get_fallback_response(
                    ErrorType.RECORDING_ISSUE, session.language
                )
                return self._generate_recording_too_long_xml(session.language)
            
            # Check recording URL
            if not recording_url or not recording_url.strip():
                logger.error(f"No recording URL provided for {from_number}")
                error_response = error_handler.get_fallback_response(
                    ErrorType.RECORDING_ISSUE, session.language
                )
                return self._generate_recording_failed_xml(session.language)
            
            # Store recording info in session
            session.current_recording_url = recording_url
            session.current_recording_duration = duration
            
            # Update menu state and processing status
            self.session_manager.update_session_menu(from_number, self.MENU_STATES['processing_question'])
            self.session_manager.update_processing_status(from_number, 'processing_audio')
            
            # Start processing pipeline in background thread with error handling
            processing_thread = threading.Thread(
                target=self._process_question_background_with_error_handling,
                args=(from_number, recording_url, session.language)
            )
            processing_thread.daemon = True
            processing_thread.start()
            
            # Generate processing message XML with polling
            xml_response = self._generate_processing_xml(session.language)
            
            logger.info(f"Started background processing for {from_number}")
            return Response(xml_response, mimetype='application/xml')
            
        except Exception as e:
            # Handle unexpected errors
            session = self.session_manager.get_session(from_number)
            language = session.language if session else 'english'
            
            error_response = error_handler.handle_error(
                error=e,
                component='IVR_QuestionRecording',
                phone_number=from_number,
                language=language
            )
            
            return self._generate_error_xml(error_response['message'])
    
    def _process_question_background(self, phone_number: str, recording_url: str, language: str):
        """
        Process question in background thread
        
        Args:
            phone_number: User's phone number
            recording_url: URL of recorded question
            language: User's language preference
        """
        try:
            logger.info(f"Background processing started for {phone_number}")
            
            # Update status
            self.session_manager.update_processing_status(phone_number, 'generating_response')
            
            # Process through pipeline
            result = self.processing_pipeline.process_question_sync(recording_url, language, phone_number)
            
            if result.success:
                # Store response data in session
                response_data = ResponseData(
                    question_text=result.question_text,
                    response_text=result.response_text,
                    response_audio_url=result.response_audio_url,
                    detailed_response_text=result.detailed_response_text,
                    detailed_audio_url=result.detailed_audio_url,
                    language=language
                )
                
                self.session_manager.store_response_data(phone_number, response_data)
                self.session_manager.update_processing_status(phone_number, 'ready')
                
                # Add to session history
                self.session_manager.add_question_to_session(phone_number, result.question_text)
                self.session_manager.add_response_to_session(phone_number, result.response_text)
                
                # Add to call recording
                try:
                    call_recorder.add_question(phone_number, result.question_text)
                    call_recorder.add_response(phone_number, result.response_text)
                    if hasattr(result, 'processing_time'):
                        call_recorder.add_processing_metrics(phone_number, {
                            'total_time': result.processing_time,
                            'stt_time': getattr(result, 'stt_time', 0),
                            'rag_time': getattr(result, 'rag_time', 0),
                            'tts_time': getattr(result, 'tts_time', 0)
                        })
                except Exception as recording_error:
                    logger.warning(f"Failed to add to call recording: {recording_error}")
                
                logger.info(f"Processing completed successfully for {phone_number}")
                
            else:
                logger.error(f"Processing failed for {phone_number}: {result.error_message}")
                self.session_manager.update_processing_status(phone_number, 'error')
                
        except Exception as e:
            logger.error(f"Background processing failed for {phone_number}: {e}")
            self.session_manager.update_processing_status(phone_number, 'error')
    
    def _process_question_background_with_error_handling(self, phone_number: str, recording_url: str, language: str):
        """
        Process question in background thread with enhanced error handling
        
        Args:
            phone_number: User's phone number
            recording_url: URL of recorded question
            language: User's language preference
        """
        try:
            logger.info(f"Background processing started for {phone_number}")
            
            # Update status
            self.session_manager.update_processing_status(phone_number, 'generating_response')
            
            # Process through pipeline with retry logic
            max_retries = 2
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    result = self.processing_pipeline.process_question_sync(recording_url, language, phone_number)
                    
                    if result.success:
                        # Store response data in session
                        response_data = ResponseData(
                            question_text=result.question_text,
                            response_text=result.response_text,
                            response_audio_url=result.response_audio_url,
                            detailed_response_text=result.detailed_response_text,
                            detailed_audio_url=result.detailed_audio_url,
                            language=language
                        )
                        
                        self.session_manager.store_response_data(phone_number, response_data)
                        self.session_manager.update_processing_status(phone_number, 'ready')
                        
                        # Add to session history
                        self.session_manager.add_question_to_session(phone_number, result.question_text)
                        self.session_manager.add_response_to_session(phone_number, result.response_text)
                        
                        logger.info(f"Processing completed successfully for {phone_number} on attempt {attempt + 1}")
                        return
                    else:
                        # Processing failed, but not an exception
                        logger.warning(f"Processing failed for {phone_number} on attempt {attempt + 1}: {result.error_message}")
                        last_error = Exception(result.error_message)
                        
                        if attempt < max_retries - 1:
                            time.sleep(1.0)  # Brief delay before retry
                            continue
                        else:
                            break
                            
                except Exception as e:
                    logger.error(f"Processing attempt {attempt + 1} failed for {phone_number}: {e}")
                    last_error = e
                    
                    if attempt < max_retries - 1:
                        time.sleep(1.0)  # Brief delay before retry
                        continue
                    else:
                        break
            
            # All attempts failed
            logger.error(f"All processing attempts failed for {phone_number}")
            
            # Track the error
            if last_error:
                error_tracker.track_error(
                    component='Background_Processing',
                    error=last_error,
                    phone_number=phone_number,
                    recovery_action=f'Failed after {max_retries} attempts'
                )
            
            # Store error information for later retrieval
            self.session_manager.update_processing_status(phone_number, 'error')
            
            # Store fallback error message
            error_response = error_handler.get_fallback_response(
                ErrorType.PROCESSING_TIMEOUT, language
            )
            
            # Store minimal response data for error handling
            error_response_data = ResponseData(
                question_text="",
                response_text=error_response['message'],
                response_audio_url="",
                detailed_response_text="",
                detailed_audio_url="",
                language=language
            )
            self.session_manager.store_response_data(phone_number, error_response_data)
                
        except Exception as e:
            logger.error(f"Critical error in background processing for {phone_number}: {e}")
            
            # Track critical error
            error_tracker.track_error(
                component='Background_Processing_Critical',
                error=e,
                phone_number=phone_number,
                recovery_action='Set error status and fallback response'
            )
            
            self.session_manager.update_processing_status(phone_number, 'error')
    
    def handle_response_delivery(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle delivery of AI-generated response with enhanced error handling
        
        Args:
            request_data: Webhook payload (response audio URL comes from session data)
            
        Returns:
            XML response with follow-up menu or appropriate error handling
        """
        from_number = request_data.get('From', 'unknown')
        
        try:
            # Get session with error handling
            session = self.session_manager.get_session(from_number)
            if not session:
                error_response = error_handler.get_fallback_response(
                    ErrorType.SYSTEM_ERROR, 'english'
                )
                return self._generate_error_xml(error_response['message'])
            
            # Check processing status with enhanced handling
            if session.processing_status == 'error':
                logger.error(f"Processing failed for {from_number}")
                error_response = error_handler.get_fallback_response(
                    ErrorType.PROCESSING_TIMEOUT, session.language
                )
                return self._generate_processing_error_xml(session.language)
            
            elif session.processing_status in ['processing_audio', 'generating_response']:
                # Still processing, check how long it's been
                processing_time = (datetime.now() - session.last_activity).total_seconds()
                
                if processing_time > 15:  # Extended timeout for demo reliability
                    logger.error(f"Processing timeout for {from_number} after {processing_time}s")
                    
                    # Track timeout error
                    error_tracker.track_error(
                        component='Response_Delivery_Timeout',
                        error=Exception(f"Processing timeout after {processing_time}s"),
                        phone_number=from_number,
                        recovery_action='Redirect to timeout error handling'
                    )
                    
                    self.session_manager.update_processing_status(from_number, 'error')
                    return self._generate_timeout_error_xml(session.language)
                else:
                    # Still within acceptable time, continue waiting
                    logger.info(f"Still processing for {from_number}, status: {session.processing_status}, time: {processing_time}s")
                    return Response(self._generate_still_processing_xml(session.language), mimetype='application/xml')
            
            elif session.processing_status != 'ready':
                # Unknown status, redirect back to processing
                logger.warning(f"Unknown processing status for {from_number}: {session.processing_status}")
                return Response(self._generate_processing_xml(session.language), mimetype='application/xml')
            
            # Get response data with validation
            response_data = self.session_manager.get_current_response_data(from_number)
            if not response_data:
                logger.error(f"No response data found for {from_number}")
                error_response = error_handler.get_fallback_response(
                    ErrorType.CONTENT_NOT_FOUND, session.language
                )
                return self._generate_no_response_error_xml(session.language)
            
            # Validate response content
            if not response_data.response_text and not response_data.response_audio_url:
                logger.error(f"No response content found for {from_number}")
                error_response = error_handler.get_fallback_response(
                    ErrorType.CONTENT_NOT_FOUND, session.language
                )
                return self._generate_no_response_error_xml(session.language)
            
            # Handle missing audio URL gracefully
            if not response_data.response_audio_url:
                logger.warning(f"No audio URL found for {from_number}, using text fallback")
                
                # Track audio generation failure
                error_tracker.track_error(
                    component='Audio_Generation_Missing',
                    error=Exception("Response audio URL not available"),
                    phone_number=from_number,
                    recovery_action='Fallback to text-to-speech'
                )
                
                return self._generate_audio_error_xml(session.language, response_data.response_text)
            
            logger.info(f"Delivering response to {from_number}: {response_data.response_audio_url}")
            
            # Update menu state
            self.session_manager.update_session_menu(from_number, self.MENU_STATES['follow_up_menu'])
            
            # Generate response delivery with follow-up menu XML
            xml_response = self._generate_response_delivery_xml(response_data.response_audio_url, session.language)
            
            logger.info(f"Response delivered successfully to {from_number}")
            return Response(xml_response, mimetype='application/xml')
            
        except Exception as e:
            # Handle unexpected errors in response delivery
            session = self.session_manager.get_session(from_number)
            language = session.language if session else 'english'
            
            error_response = error_handler.handle_error(
                error=e,
                component='IVR_ResponseDelivery',
                phone_number=from_number,
                language=language
            )
            
            logger.error(f"Error in response delivery for {from_number}: {error_response}")
            return self._generate_error_xml(error_response['message'])
    
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
            
            # Get current response data
            response_data = self.session_manager.get_current_response_data(from_number)
            if not response_data:
                logger.error(f"No response data found for follow-up menu: {from_number}")
                return self._generate_error_xml("Sorry, no previous response found. Please ask a new question.")
            
            logger.info(f"Follow-up menu selection from {from_number}: {digits}")
            
            if digits == '1':  # Detailed explanation
                if response_data.detailed_audio_url:
                    xml_response = self._generate_detailed_explanation_xml(response_data.detailed_audio_url, session.language)
                else:
                    # Generate detailed explanation if not available
                    xml_response = self._generate_processing_detailed_xml(session.language)
                    # Start background processing for detailed explanation (async)
                    detailed_thread = threading.Thread(
                        target=self._generate_detailed_explanation_background,
                        args=(from_number, response_data)
                    )
                    detailed_thread.daemon = True
                    detailed_thread.start()
                
                return Response(xml_response, mimetype='application/xml')
            
            elif digits == '2':  # Repeat answer
                # Replay the original response
                xml_response = self._generate_repeat_response_xml(response_data.response_audio_url, session.language)
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
    
    def _generate_detailed_explanation_background(self, phone_number: str, response_data: ResponseData):
        """
        Generate detailed explanation in background if not already available
        
        Args:
            phone_number: User's phone number
            response_data: Current response data
        """
        try:
            if response_data.detailed_audio_url:
                return  # Already have detailed explanation
            
            logger.info(f"Generating detailed explanation for {phone_number}")
            
            # Use the processing pipeline to generate detailed response
            # This is a simplified version - in practice, you might want to 
            # store the original question and regenerate with detailed context
            from src.audio.audio_processor import Language
            from src.rag.context_builder import ContextBuilder
            from src.rag.response_generator import ResponseGenerator
            
            language_enum = Language.TELUGU if response_data.language == 'telugu' else Language.ENGLISH
            
            # Build detailed context
            context_builder = ContextBuilder(self.config)
            detailed_context = context_builder.build_context(
                question=response_data.question_text,
                language=response_data.language,
                detail_level="detailed"
            )
            
            # Generate detailed response
            response_generator = ResponseGenerator(self.config)
            detailed_result = response_generator.generate_response(detailed_context)
            
            if detailed_result['success']:
                # Convert to audio
                detailed_audio_result = self.processing_pipeline.audio_processor.generate_response_audio(
                    detailed_result['response_text'], 
                    language_enum
                )
                
                if detailed_audio_result.success:
                    # Upload audio
                    detailed_audio_url = self.processing_pipeline._upload_audio_for_ivr(
                        detailed_audio_result.audio_data,
                        f"detailed_{phone_number}_{int(time.time())}"
                    )
                    
                    # Update response data
                    response_data.detailed_response_text = detailed_result['response_text']
                    response_data.detailed_audio_url = detailed_audio_url
                    
                    self.session_manager.store_response_data(phone_number, response_data)
                    
                    logger.info(f"Detailed explanation generated for {phone_number}")
                
        except Exception as e:
            logger.error(f"Failed to generate detailed explanation for {phone_number}: {e}")
    
    def handle_error_recovery(self, request_data: Dict[str, Any]) -> Response:
        """
        Handle error recovery menu selections
        
        Args:
            request_data: Webhook payload with DTMF digits
            
        Returns:
            XML response based on recovery selection
        """
        return self.error_recovery_handler.handle_error_recovery(request_data)
    
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
            
            # End call recording
            try:
                recording_id = call_recorder.end_recording(from_number, 'completed')
                if recording_id:
                    logger.info(f"Ended call recording {recording_id} for {from_number}")
            except Exception as recording_error:
                logger.warning(f"Failed to end call recording: {recording_error}")
            
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
        """Generate processing message XML with polling"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "Thank you for your question. I am processing it now. This may take up to 8 seconds. Please wait."
        else:  # telugu
            voice = 'alice'
            lang = 'en-IN'
            message = "మీ ప్రశ్నకు ధన్యవాదాలు. నేను దానిని ఇప్పుడు ప్రాసెస్ చేస్తున్నాను. దయచేసి 8 సెకన్లు వేచి ఉండండి."
        
        # Processing message
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Pause for processing (shorter initial pause)
        pause = ET.SubElement(root, 'Pause', length='3')
        
        # Redirect to check processing status
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
    
    def _generate_detailed_explanation_xml(self, detailed_audio_url: str, language: str) -> str:
        """Generate XML for detailed explanation playback"""
        root = ET.Element('Response')
        
        # Play the detailed explanation
        if detailed_audio_url:
            play = ET.SubElement(root, 'Play')
            play.text = detailed_audio_url
        else:
            # Fallback message
            say = ET.SubElement(root, 'Say', voice='alice', language='en-IN')
            if language == 'english':
                say.text = "I apologize, but I couldn't generate a detailed explanation. Let me repeat the original answer."
            else:
                say.text = "క్షమించండి, వివరణాత్మక సమాధానం జనరేట్ చేయలేకపోయాను. అసలు సమాధానం మళ్లీ వినండి."
        
        # Return to follow-up menu
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            menu_message = "Press 2 to hear the answer again, Press 3 for new question, or Press 9 for main menu."
        else:
            voice = 'alice'
            lang = 'en-IN'
            menu_message = "మళ్లీ వినడానికి 2 నొక్కండి, కొత్త ప్రశ్న కోసం 3 నొక్కండి, లేదా మెయిన్ మెనూ కోసం 9 నొక్కండి."
        
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
    
    def _generate_repeat_response_xml(self, response_audio_url: str, language: str) -> str:
        """Generate XML for repeating the response"""
        root = ET.Element('Response')
        
        # Play the original response again
        if response_audio_url:
            play = ET.SubElement(root, 'Play')
            play.text = response_audio_url
        else:
            # Fallback message
            say = ET.SubElement(root, 'Say', voice='alice', language='en-IN')
            if language == 'english':
                say.text = "I apologize, but I cannot replay the previous answer. Please ask your question again."
            else:
                say.text = "క్షమించండి, మునుపటి సమాధానం మళ్లీ ప్లే చేయలేను. దయచేసి మీ ప్రశ్నను మళ్లీ అడగండి."
        
        # Return to follow-up menu
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            menu_message = "Press 1 for detailed explanation, Press 3 for new question, or Press 9 for main menu."
        else:
            voice = 'alice'
            lang = 'en-IN'
            menu_message = "వివరణ కోసం 1 నొక్కండి, కొత్త ప్రశ్న కోసం 3 నొక్కండి, లేదా మెయిన్ మెనూ కోసం 9 నొక్కండి."
        
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
    
    def _generate_processing_detailed_xml(self, language: str) -> str:
        """Generate processing message for detailed explanation"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "Generating detailed explanation. Please wait a moment."
        else:
            voice = 'alice'
            lang = 'en-IN'
            message = "వివరణాత్మక సమాధానం తయారు చేస్తున్నాను. దయచేసి కాసేపు వేచి ఉండండి."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        pause = ET.SubElement(root, 'Pause', length='3')
        
        # Redirect back to follow-up menu (detailed explanation should be ready by then)
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/follow-up-menu'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_still_processing_xml(self, language: str) -> str:
        """Generate XML for continued processing"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "Still processing your question. Please wait a few more seconds."
        else:
            voice = 'alice'
            lang = 'en-IN'
            message = "మీ ప్రశ్నను ఇంకా ప్రాసెస్ చేస్తున్నాను. దయచేసి మరికొన్ని సెకన్లు వేచి ఉండండి."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        pause = ET.SubElement(root, 'Pause', length='3')
        
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/response-delivery'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_processing_error_xml(self, language: str) -> str:
        """Generate XML for processing errors with retry option"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "I'm sorry, I had trouble processing your question. Press 1 to try asking again or Press 9 for main menu."
        else:
            voice = 'alice'
            lang = 'en-IN'
            message = "క్షమించండి, మీ ప్రశ్నను ప్రాసెస్ చేయడంలో సమస్య ఉంది. మళ్లీ ప్రయత్నించడానికి 1 నొక్కండి లేదా మెయిన్ మెనూ కోసం 9 నొక్కండి."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        gather = ET.SubElement(root, 'Gather',
                              numDigits='1',
                              timeout='10',
                              action='/webhook/error-recovery',
                              method='POST')
        
        # Fallback to main menu
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/interaction-mode'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_timeout_error_xml(self, language: str) -> str:
        """Generate XML for processing timeout"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "I'm taking longer than expected to process your question. Press 1 to try a simpler question or Press 9 for main menu."
        else:
            voice = 'alice'
            lang = 'en-IN'
            message = "మీ ప్రశ్నను ప్రాసెస్ చేయడానికి ఊహించిన దానికంటే ఎక్కువ సమయం పడుతోంది. సరళమైన ప్రశ్న అడగడానికి 1 నొక్కండి లేదా మెయిన్ మెనూ కోసం 9 నొక్కండి."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        gather = ET.SubElement(root, 'Gather',
                              numDigits='1',
                              timeout='10',
                              action='/webhook/error-recovery',
                              method='POST')
        
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/interaction-mode'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_no_response_error_xml(self, language: str) -> str:
        """Generate XML when no response data is available"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "I couldn't generate an answer to your question. Please try asking a different Class 10 Science question."
        else:
            voice = 'alice'
            lang = 'en-IN'
            message = "మీ ప్రశ్నకు సమాధానం రూపొందించలేకపోయాను. దయచేసి వేరే క్లాస్ 10 సైన్స్ ప్రశ్న అడగండి."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Redirect to question recording
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/interaction-mode-selection'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_audio_error_xml(self, language: str, response_text: str) -> str:
        """Generate XML when audio generation fails but we have text response"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            fallback_message = "I couldn't generate audio for my response, but here's the answer: "
        else:
            voice = 'alice'
            lang = 'en-IN'
            fallback_message = "నా సమాధానానికి ఆడియో రూపొందించలేకపోయాను, కానీ ఇదిగో సమాధానం: "
        
        # Fallback to text-to-speech of the response
        say_intro = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say_intro.text = fallback_message
        
        say_response = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say_response.text = response_text[:200]  # Limit length for voice delivery
        
        # Continue to follow-up menu
        if language == 'english':
            menu_message = "Press 1 for detailed explanation, Press 3 for new question, or Press 9 for main menu."
        else:
            menu_message = "వివరణ కోసం 1 నొక్కండి, కొత్త ప్రశ్న కోసం 3 నొక్కండి, లేదా మెయిన్ మెనూ కోసం 9 నొక్కండి."
        
        gather = ET.SubElement(root, 'Gather',
                              numDigits='1',
                              timeout='15',
                              action='/webhook/follow-up-menu',
                              method='POST')
        
        say_gather = ET.SubElement(gather, 'Say', voice=voice, language=lang)
        say_gather.text = menu_message
        
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/interaction-mode'
        
        return ET.tostring(root, encoding='unicode')

    def _generate_recording_too_short_xml(self, language: str) -> str:
        """Generate XML for recording too short error"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "Your recording was too short. Please speak for at least 2 seconds. Let's try again."
        else:
            voice = 'alice'
            lang = 'en-IN'
            message = "మీ రికార్డింగ్ చాలా చిన్నది. దయచేసి కనీసం 2 సెకన్లు మాట్లాడండి. మళ్లీ ప్రయత్నిద్దాం."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Redirect back to question recording
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/interaction-mode-selection'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_recording_too_long_xml(self, language: str) -> str:
        """Generate XML for recording too long error"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "Your recording was too long. Please ask a shorter question in 15 seconds or less."
        else:
            voice = 'alice'
            lang = 'en-IN'
            message = "మీ రికార్డింగ్ చాలా పొడవుగా ఉంది. దయచేసి 15 సెకన్లలో లేదా అంతకంటే తక్కువ సమయంలో చిన్న ప్రశ్న అడగండి."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Redirect back to question recording
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/interaction-mode-selection'
        
        return ET.tostring(root, encoding='unicode')
    
    def _generate_recording_failed_xml(self, language: str) -> str:
        """Generate XML for recording failure"""
        root = ET.Element('Response')
        
        if language == 'english':
            voice = 'alice'
            lang = 'en-IN'
            message = "There was a problem with your recording. Please try asking your question again."
        else:
            voice = 'alice'
            lang = 'en-IN'
            message = "మీ రికార్డింగ్‌లో సమస్య ఉంది. దయచేసి మీ ప్రశ్నను మళ్లీ అడగండి."
        
        say = ET.SubElement(root, 'Say', voice=voice, language=lang)
        say.text = message
        
        # Redirect back to question recording
        redirect = ET.SubElement(root, 'Redirect', method='POST')
        redirect.text = '/webhook/interaction-mode-selection'
        
        return ET.tostring(root, encoding='unicode')

    def _generate_error_xml(self, error_message: str) -> str:
        """Generate error XML response"""
        root = ET.Element('Response')
        
        say = ET.SubElement(root, 'Say', voice='alice', language='en-IN')
        say.text = error_message
        
        hangup = ET.SubElement(root, 'Hangup')
        
        return ET.tostring(root, encoding='unicode')