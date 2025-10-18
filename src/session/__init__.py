"""
Session management module for VidyaVani IVR Learning System
"""

from .session_manager import SessionManager, UserSession, session_manager
from .session_utils import (
    get_or_create_user_session,
    process_user_question,
    process_system_response,
    update_user_menu_state,
    get_session_info,
    handle_call_end,
    get_demo_question_list,
    is_demo_question,
    cache_audio_for_response,
    get_cached_audio_response,
    get_system_stats
)

__all__ = [
    'SessionManager', 
    'UserSession', 
    'session_manager',
    'get_or_create_user_session',
    'process_user_question',
    'process_system_response',
    'update_user_menu_state',
    'get_session_info',
    'handle_call_end',
    'get_demo_question_list',
    'is_demo_question',
    'cache_audio_for_response',
    'get_cached_audio_response',
    'get_system_stats'
]