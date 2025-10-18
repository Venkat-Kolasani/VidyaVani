"""
Call Recording Functionality for VidyaVani IVR Learning System
Handles recording, storage, and playback of demo calls for presentation
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)

@dataclass
class CallRecording:
    """Data structure for call recording metadata"""
    recording_id: str
    phone_number: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    language: str
    questions_asked: List[str]
    responses_given: List[str]
    audio_files: List[str]  # List of audio file paths
    processing_metrics: Dict[str, Any]
    call_status: str  # 'active', 'completed', 'error'
    demo_mode: bool
    created_at: datetime

class CallRecorder:
    """Manages call recording for demo and debugging purposes"""
    
    def __init__(self, storage_dir: str = "call_recordings"):
        self.storage_dir = storage_dir
        self.recordings: Dict[str, CallRecording] = {}
        self.active_recordings: Dict[str, str] = {}  # phone_number -> recording_id
        
        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "audio"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "metadata"), exist_ok=True)
        
        logger.info(f"CallRecorder initialized with storage: {self.storage_dir}")
    
    def start_recording(self, phone_number: str, session_id: str, 
                       language: str = "english", demo_mode: bool = False) -> str:
        """Start recording a call session"""
        try:
            recording_id = str(uuid.uuid4())
            
            recording = CallRecording(
                recording_id=recording_id,
                phone_number=phone_number,
                session_id=session_id,
                start_time=datetime.now(timezone.utc),
                end_time=None,
                duration_seconds=None,
                language=language,
                questions_asked=[],
                responses_given=[],
                audio_files=[],
                processing_metrics={},
                call_status='active',
                demo_mode=demo_mode,
                created_at=datetime.now(timezone.utc)
            )
            
            self.recordings[recording_id] = recording
            self.active_recordings[phone_number] = recording_id
            
            logger.info(f"Started recording for {phone_number}: {recording_id}")
            return recording_id
            
        except Exception as e:
            logger.error(f"Error starting recording: {str(e)}")
            raise
    
    def add_question(self, phone_number: str, question: str) -> bool:
        """Add a question to the active recording"""
        try:
            recording_id = self.active_recordings.get(phone_number)
            if not recording_id:
                logger.warning(f"No active recording for {phone_number}")
                return False
            
            recording = self.recordings.get(recording_id)
            if recording:
                recording.questions_asked.append(question)
                logger.debug(f"Added question to recording {recording_id}: {question[:50]}...")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding question to recording: {str(e)}")
            return False
    
    def add_response(self, phone_number: str, response: str) -> bool:
        """Add a response to the active recording"""
        try:
            recording_id = self.active_recordings.get(phone_number)
            if not recording_id:
                logger.warning(f"No active recording for {phone_number}")
                return False
            
            recording = self.recordings.get(recording_id)
            if recording:
                recording.responses_given.append(response)
                logger.debug(f"Added response to recording {recording_id}: {response[:50]}...")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding response to recording: {str(e)}")
            return False
    
    def add_audio_file(self, phone_number: str, audio_file_path: str) -> bool:
        """Add an audio file to the active recording"""
        try:
            recording_id = self.active_recordings.get(phone_number)
            if not recording_id:
                logger.warning(f"No active recording for {phone_number}")
                return False
            
            recording = self.recordings.get(recording_id)
            if recording:
                recording.audio_files.append(audio_file_path)
                logger.debug(f"Added audio file to recording {recording_id}: {audio_file_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding audio file to recording: {str(e)}")
            return False
    
    def add_processing_metrics(self, phone_number: str, metrics: Dict[str, Any]) -> bool:
        """Add processing metrics to the active recording"""
        try:
            recording_id = self.active_recordings.get(phone_number)
            if not recording_id:
                logger.warning(f"No active recording for {phone_number}")
                return False
            
            recording = self.recordings.get(recording_id)
            if recording:
                recording.processing_metrics.update(metrics)
                logger.debug(f"Added metrics to recording {recording_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding metrics to recording: {str(e)}")
            return False
    
    def end_recording(self, phone_number: str, status: str = "completed") -> Optional[str]:
        """End the active recording for a phone number"""
        try:
            recording_id = self.active_recordings.get(phone_number)
            if not recording_id:
                logger.warning(f"No active recording for {phone_number}")
                return None
            
            recording = self.recordings.get(recording_id)
            if recording:
                recording.end_time = datetime.now(timezone.utc)
                recording.duration_seconds = (recording.end_time - recording.start_time).total_seconds()
                recording.call_status = status
                
                # Save recording metadata to file
                self._save_recording_metadata(recording)
                
                # Remove from active recordings
                del self.active_recordings[phone_number]
                
                logger.info(f"Ended recording {recording_id} for {phone_number} (duration: {recording.duration_seconds:.1f}s)")
                return recording_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error ending recording: {str(e)}")
            return None
    
    def get_recording(self, recording_id: str) -> Optional[CallRecording]:
        """Get a specific recording by ID"""
        return self.recordings.get(recording_id)
    
    def get_active_recording(self, phone_number: str) -> Optional[CallRecording]:
        """Get the active recording for a phone number"""
        recording_id = self.active_recordings.get(phone_number)
        if recording_id:
            return self.recordings.get(recording_id)
        return None
    
    def list_recordings(self, demo_only: bool = False, limit: int = 50) -> List[CallRecording]:
        """List all recordings, optionally filtered by demo mode"""
        recordings = list(self.recordings.values())
        
        if demo_only:
            recordings = [r for r in recordings if r.demo_mode]
        
        # Sort by creation time (newest first)
        recordings.sort(key=lambda x: x.created_at, reverse=True)
        
        return recordings[:limit]
    
    def get_demo_recordings(self) -> List[CallRecording]:
        """Get all demo recordings for presentation"""
        return self.list_recordings(demo_only=True)
    
    def export_recording(self, recording_id: str, export_path: Optional[str] = None) -> str:
        """Export a recording to JSON file"""
        try:
            recording = self.recordings.get(recording_id)
            if not recording:
                raise ValueError(f"Recording {recording_id} not found")
            
            if not export_path:
                timestamp = recording.created_at.strftime("%Y%m%d_%H%M%S")
                export_path = os.path.join(
                    self.storage_dir, 
                    f"export_recording_{recording_id[:8]}_{timestamp}.json"
                )
            
            # Convert recording to dict with datetime serialization
            recording_dict = asdict(recording)
            recording_dict['start_time'] = recording.start_time.isoformat()
            recording_dict['end_time'] = recording.end_time.isoformat() if recording.end_time else None
            recording_dict['created_at'] = recording.created_at.isoformat()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(recording_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported recording {recording_id} to {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Error exporting recording: {str(e)}")
            raise
    
    def create_demo_summary(self) -> Dict[str, Any]:
        """Create a summary of demo recordings for presentation"""
        try:
            demo_recordings = self.get_demo_recordings()
            
            if not demo_recordings:
                return {
                    'total_demos': 0,
                    'message': 'No demo recordings available'
                }
            
            total_duration = sum(r.duration_seconds or 0 for r in demo_recordings)
            total_questions = sum(len(r.questions_asked) for r in demo_recordings)
            
            # Calculate average processing times
            processing_times = []
            for recording in demo_recordings:
                if recording.processing_metrics.get('total_time'):
                    processing_times.append(recording.processing_metrics['total_time'])
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Language distribution
            languages = {}
            for recording in demo_recordings:
                lang = recording.language
                languages[lang] = languages.get(lang, 0) + 1
            
            summary = {
                'total_demos': len(demo_recordings),
                'total_duration_minutes': total_duration / 60,
                'total_questions': total_questions,
                'average_processing_time': avg_processing_time,
                'language_distribution': languages,
                'success_rate': len([r for r in demo_recordings if r.call_status == 'completed']) / len(demo_recordings) * 100,
                'recordings': [
                    {
                        'id': r.recording_id,
                        'phone_number': r.phone_number,
                        'duration': r.duration_seconds,
                        'questions': len(r.questions_asked),
                        'language': r.language,
                        'status': r.call_status,
                        'created_at': r.created_at.isoformat()
                    }
                    for r in demo_recordings
                ]
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating demo summary: {str(e)}")
            return {'error': str(e)}
    
    def _save_recording_metadata(self, recording: CallRecording) -> None:
        """Save recording metadata to file"""
        try:
            metadata_path = os.path.join(
                self.storage_dir, 
                "metadata", 
                f"{recording.recording_id}.json"
            )
            
            # Convert to dict with datetime serialization
            recording_dict = asdict(recording)
            recording_dict['start_time'] = recording.start_time.isoformat()
            recording_dict['end_time'] = recording.end_time.isoformat() if recording.end_time else None
            recording_dict['created_at'] = recording.created_at.isoformat()
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(recording_dict, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved recording metadata: {metadata_path}")
            
        except Exception as e:
            logger.error(f"Error saving recording metadata: {str(e)}")
    
    def cleanup_old_recordings(self, days_old: int = 7) -> int:
        """Clean up recordings older than specified days"""
        try:
            cutoff_date = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=days_old)
            
            removed_count = 0
            recordings_to_remove = []
            
            for recording_id, recording in self.recordings.items():
                if recording.created_at < cutoff_date and not recording.demo_mode:
                    recordings_to_remove.append(recording_id)
            
            for recording_id in recordings_to_remove:
                # Remove metadata file
                metadata_path = os.path.join(
                    self.storage_dir, 
                    "metadata", 
                    f"{recording_id}.json"
                )
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                
                # Remove from memory
                del self.recordings[recording_id]
                removed_count += 1
            
            logger.info(f"Cleaned up {removed_count} old recordings")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up recordings: {str(e)}")
            return 0

# Global call recorder instance
call_recorder = CallRecorder()