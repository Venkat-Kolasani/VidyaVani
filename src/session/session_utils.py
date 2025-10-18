"""
Session utility functions for VidyaVani IVR Learning System
Helper functions for common session operations
"""

from typing import Optional, Dict, Any
from .session_manager import session_manager
import logging

logger = logging.getLogger(__name__)

def get_or_create_user_session(phone_number: str, language: str = "english"):
    """
    Get existing session or create new one with language preference
    
    Args:
        phone_number: User's phone number
        language: Preferred language (english/telugu)
    
    Returns:
        UserSession object
    """
    session = session_manager.get_or_create_session(phone_number)
    
    # Update language if different from current
    if session.language != language:
        session_manager.update_session_language(phone_number, language)
    
    return session

def process_user_question(phone_number: str, question: str) -> Dict[str, Any]:
    """
    Process user question and update session
    
    Args:
        phone_number: User's phone number
        question: User's question text
    
    Returns:
        Dict with question processing info
    """
    # Add question to session
    session_manager.add_question_to_session(phone_number, question)
    
    # Check for cached demo response
    cached_response = session_manager.get_cached_demo_response(question)
    
    # Get conversation context for RAG
    context = session_manager.get_conversation_context(phone_number)
    
    return {
        "question": question,
        "cached_response": cached_response,
        "conversation_context": context,
        "is_demo_question": cached_response is not None
    }

def process_system_response(phone_number: str, response: str) -> bool:
    """
    Process system response and update session
    
    Args:
        phone_number: User's phone number
        response: System's response text
    
    Returns:
        Success status
    """
    return session_manager.add_response_to_session(phone_number, response)

def update_user_menu_state(phone_number: str, menu_state: str) -> bool:
    """
    Update user's current menu state
    
    Args:
        phone_number: User's phone number
        menu_state: New menu state
    
    Returns:
        Success status
    """
    return session_manager.update_session_menu(phone_number, menu_state)

def get_session_info(phone_number: str) -> Optional[Dict[str, Any]]:
    """
    Get session information for user
    
    Args:
        phone_number: User's phone number
    
    Returns:
        Session info dict or None if not found
    """
    session = session_manager.get_session(phone_number)
    
    if not session:
        return None
    
    return {
        "session_id": session.session_id,
        "phone_number": session.phone_number,
        "language": session.language,
        "current_menu": session.current_menu,
        "question_count": len(session.question_history),
        "response_count": len(session.response_history),
        "call_active": session.call_active,
        "start_time": session.start_time.isoformat(),
        "last_activity": session.last_activity.isoformat()
    }

def handle_call_end(phone_number: str) -> bool:
    """
    Handle call end - mark session as inactive and cleanup
    
    Args:
        phone_number: User's phone number
    
    Returns:
        Success status
    """
    # End the session
    success = session_manager.end_session(phone_number)
    
    if success:
        # Clean up session from memory after a short delay
        # In production, you might want to do this asynchronously
        session_manager.cleanup_session(phone_number)
        logger.info(f"Call ended and session cleaned up for {phone_number}")
    
    return success

def get_demo_question_list() -> list:
    """
    Get list of available demo questions
    
    Returns:
        List of demo questions
    """
    return session_manager.get_demo_questions()

def is_demo_question(question: str) -> bool:
    """
    Check if question has a cached demo response
    
    Args:
        question: Question text
    
    Returns:
        True if demo question, False otherwise
    """
    return session_manager.get_cached_demo_response(question) is not None

def cache_audio_for_response(text: str, audio_data: bytes, language: str = "english"):
    """
    Cache TTS audio for faster delivery
    
    Args:
        text: Response text
        audio_data: TTS audio bytes
        language: Language of the audio
    """
    session_manager.cache_audio_response(text, audio_data, language)

def get_cached_audio_response(text: str, language: str = "english") -> Optional[bytes]:
    """
    Get cached TTS audio if available
    
    Args:
        text: Response text
        language: Language of the audio
    
    Returns:
        Audio bytes or None if not cached
    """
    return session_manager.get_cached_audio(text, language)

def get_system_stats() -> Dict[str, Any]:
    """
    Get system-wide session statistics
    
    Returns:
        Statistics dictionary
    """
    return session_manager.get_session_stats()