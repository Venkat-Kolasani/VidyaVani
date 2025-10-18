"""
Session Management for VidyaVani IVR Learning System
Handles user sessions, conversation context, and demo question caching
"""

import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from threading import Lock
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserSession:
    """User session data structure"""
    session_id: str
    phone_number: str
    language: str = "english"  # Default to English
    current_menu: str = "main"  # Current menu state
    question_history: List[str] = field(default_factory=list)
    response_history: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    call_active: bool = True
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def add_question(self, question: str):
        """Add question to history"""
        self.question_history.append(question)
        self.update_activity()
    
    def add_response(self, response: str):
        """Add response to history"""
        self.response_history.append(response)
        self.update_activity()
    
    def get_conversation_context(self) -> str:
        """Get conversation context for RAG engine"""
        if not self.question_history:
            return ""
        
        context_parts = []
        # Include last 3 Q&A pairs for context
        for i in range(max(0, len(self.question_history) - 3), len(self.question_history)):
            if i < len(self.response_history):
                context_parts.append(f"Q: {self.question_history[i]}")
                context_parts.append(f"A: {self.response_history[i]}")
        
        return "\n".join(context_parts)

class SessionManager:
    """Manages user sessions and demo question caching"""
    
    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
        self.demo_cache: Dict[str, str] = {}
        self.demo_audio_cache: Dict[str, bytes] = {}
        self._lock = Lock()
        self._initialize_demo_cache()
        logger.info("SessionManager initialized")
    
    def _initialize_demo_cache(self):
        """Initialize cache with 20 demo questions and responses"""
        demo_questions = [
            # Physics Questions (7)
            "What is reflection of light?",
            "How does a concave mirror work?",
            "What is the difference between AC and DC current?",
            "Explain Ohm's law",
            "What causes magnetic field around a wire?",
            "How do electric motors work?",
            "What is refraction of light?",
            
            # Chemistry Questions (7)
            "What happens when acid reacts with base?",
            "How is soap made from oil?",
            "What are the properties of metals?",
            "Explain the process of corrosion",
            "What is a chemical equation?",
            "How do we test for carbon dioxide gas?",
            "What is the pH scale?",
            
            # Biology Questions (6)
            "How do plants make their food?",
            "What is the function of kidneys?",
            "How does the heart pump blood?",
            "What is photosynthesis?",
            "How do we breathe?",
            "What is reproduction in plants?"
        ]
        
        # Pre-generate simple responses for demo
        demo_responses = [
            # Physics Responses
            "Reflection of light occurs when light rays bounce back from a surface. The angle of incidence equals the angle of reflection. This happens with mirrors and shiny surfaces.",
            "A concave mirror curves inward and can focus light rays to a point. It's used in car headlights and telescopes to concentrate light beams.",
            "AC current changes direction periodically, while DC current flows in one direction. AC is used in homes, DC in batteries and electronics.",
            "Ohm's law states that current equals voltage divided by resistance. It helps us calculate electrical values in circuits.",
            "When electric current flows through a wire, it creates a magnetic field around it. This is the principle behind electromagnets.",
            "Electric motors convert electrical energy to mechanical energy using magnetic fields. They work by interaction between current and magnets.",
            "Refraction is the bending of light when it passes from one medium to another, like air to water. This makes objects appear bent in water.",
            
            # Chemistry Responses
            "When acid reacts with base, they neutralize each other to form salt and water. This is called neutralization reaction.",
            "Soap is made by treating oils or fats with sodium hydroxide. This process is called saponification and produces soap and glycerol.",
            "Metals are good conductors of heat and electricity, they are malleable, ductile, and have metallic luster. Most are solid at room temperature.",
            "Corrosion is the gradual destruction of metals by chemical reaction with environment. Rusting of iron is a common example.",
            "A chemical equation shows reactants and products of a reaction using chemical formulas. It must be balanced to follow conservation of mass.",
            "Carbon dioxide turns lime water milky. We can also use pH indicators as CO2 makes solutions slightly acidic.",
            "pH scale measures how acidic or basic a solution is. It ranges from 0 to 14, with 7 being neutral.",
            
            # Biology Responses
            "Plants make food through photosynthesis. They use sunlight, carbon dioxide, and water to produce glucose and oxygen in their leaves.",
            "Kidneys filter waste products from blood and make urine. They also maintain water balance and blood pressure in our body.",
            "The heart has four chambers and pumps blood through two circuits - to lungs for oxygen and to body for nutrients.",
            "Photosynthesis is how plants convert light energy into chemical energy. Chlorophyll in leaves captures sunlight to make glucose.",
            "We breathe by expanding and contracting our lungs. Diaphragm muscle helps in this process to take in oxygen and remove carbon dioxide.",
            "Plants reproduce through flowers that contain male and female parts. Pollination leads to seed formation for new plants."
        ]
        
        # Cache the demo Q&A pairs
        for question, response in zip(demo_questions, demo_responses):
            question_hash = self._get_question_hash(question)
            self.demo_cache[question_hash] = response
        
        logger.info(f"Demo cache initialized with {len(self.demo_cache)} question-response pairs")
    
    def _get_question_hash(self, question: str) -> str:
        """Generate hash for question to use as cache key"""
        return hashlib.md5(question.lower().strip().encode()).hexdigest()
    
    def create_session(self, phone_number: str) -> UserSession:
        """Create new session for phone number"""
        with self._lock:
            session_id = f"{phone_number}_{int(time.time())}"
            session = UserSession(
                session_id=session_id,
                phone_number=phone_number
            )
            self.sessions[phone_number] = session
            logger.info(f"Created new session for {phone_number}")
            return session
    
    def get_session(self, phone_number: str) -> Optional[UserSession]:
        """Get existing session by phone number"""
        with self._lock:
            return self.sessions.get(phone_number)
    
    def get_or_create_session(self, phone_number: str) -> UserSession:
        """Get existing session or create new one"""
        session = self.get_session(phone_number)
        if session is None or not session.call_active:
            session = self.create_session(phone_number)
        else:
            session.update_activity()
        return session
    
    def update_session_language(self, phone_number: str, language: str) -> bool:
        """Update session language preference"""
        with self._lock:
            session = self.sessions.get(phone_number)
            if session:
                session.language = language
                session.update_activity()
                logger.info(f"Updated language to {language} for {phone_number}")
                return True
            return False
    
    def update_session_menu(self, phone_number: str, menu_state: str) -> bool:
        """Update current menu state"""
        with self._lock:
            session = self.sessions.get(phone_number)
            if session:
                session.current_menu = menu_state
                session.update_activity()
                return True
            return False
    
    def add_question_to_session(self, phone_number: str, question: str) -> bool:
        """Add question to session history"""
        with self._lock:
            session = self.sessions.get(phone_number)
            if session:
                session.add_question(question)
                return True
            return False
    
    def add_response_to_session(self, phone_number: str, response: str) -> bool:
        """Add response to session history"""
        with self._lock:
            session = self.sessions.get(phone_number)
            if session:
                session.add_response(response)
                return True
            return False
    
    def get_cached_demo_response(self, question: str) -> Optional[str]:
        """Get cached response for demo question"""
        question_hash = self._get_question_hash(question)
        return self.demo_cache.get(question_hash)
    
    def cache_audio_response(self, text: str, audio_data: bytes, language: str = "english"):
        """Cache TTS audio for faster delivery"""
        cache_key = f"{language}_{self._get_question_hash(text)}"
        self.demo_audio_cache[cache_key] = audio_data
        logger.debug(f"Cached audio response for key: {cache_key}")
    
    def get_cached_audio(self, text: str, language: str = "english") -> Optional[bytes]:
        """Get cached TTS audio"""
        cache_key = f"{language}_{self._get_question_hash(text)}"
        return self.demo_audio_cache.get(cache_key)
    
    def end_session(self, phone_number: str) -> bool:
        """End session when call ends"""
        with self._lock:
            session = self.sessions.get(phone_number)
            if session:
                session.call_active = False
                session.update_activity()
                logger.info(f"Ended session for {phone_number}")
                return True
            return False
    
    def cleanup_session(self, phone_number: str) -> bool:
        """Remove session from memory (call this after call ends)"""
        with self._lock:
            if phone_number in self.sessions:
                del self.sessions[phone_number]
                logger.info(f"Cleaned up session for {phone_number}")
                return True
            return False
    
    def get_conversation_context(self, phone_number: str) -> str:
        """Get conversation context for RAG engine"""
        session = self.get_session(phone_number)
        if session:
            return session.get_conversation_context()
        return ""
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics for monitoring"""
        with self._lock:
            active_sessions = sum(1 for s in self.sessions.values() if s.call_active)
            total_sessions = len(self.sessions)
            demo_cache_size = len(self.demo_cache)
            audio_cache_size = len(self.demo_audio_cache)
            
            return {
                "active_sessions": active_sessions,
                "total_sessions": total_sessions,
                "demo_cache_size": demo_cache_size,
                "audio_cache_size": audio_cache_size,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_demo_questions(self) -> List[str]:
        """Get list of all demo questions for testing"""
        # Reverse lookup from cache to get original questions
        demo_questions = [
            "What is reflection of light?",
            "How does a concave mirror work?",
            "What is the difference between AC and DC current?",
            "Explain Ohm's law",
            "What causes magnetic field around a wire?",
            "How do electric motors work?",
            "What is refraction of light?",
            "What happens when acid reacts with base?",
            "How is soap made from oil?",
            "What are the properties of metals?",
            "Explain the process of corrosion",
            "What is a chemical equation?",
            "How do we test for carbon dioxide gas?",
            "What is the pH scale?",
            "How do plants make their food?",
            "What is the function of kidneys?",
            "How does the heart pump blood?",
            "What is photosynthesis?",
            "How do we breathe?",
            "What is reproduction in plants?"
        ]
        return demo_questions

# Global session manager instance
session_manager = SessionManager()