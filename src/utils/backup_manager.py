"""
Backup and recovery manager for VidyaVani IVR Learning System
Handles FAISS index, cached data, and system state backup/recovery
"""

import os
import json
import shutil
import tarfile
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading
import time

@dataclass
class BackupInfo:
    """Backup information structure"""
    backup_id: str
    timestamp: datetime
    backup_type: str  # full, incremental, faiss_only, cache_only
    file_path: str
    size_bytes: int
    components: List[str]
    status: str  # created, verified, corrupted, restored
    metadata: Dict[str, Any] = None

class BackupManager:
    """Manages backup and recovery operations"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Backup configuration
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        # Retention policy
        self.max_backups = int(os.getenv('MAX_BACKUPS', '10'))
        self.backup_retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '7'))
        
        # Auto-backup settings
        self.auto_backup_enabled = os.getenv('AUTO_BACKUP_ENABLED', 'true').lower() == 'true'
        self.auto_backup_interval = int(os.getenv('AUTO_BACKUP_INTERVAL_HOURS', '6'))
        
        # Backup history
        self.backup_history: List[BackupInfo] = []
        self.load_backup_history()
        
        # Auto-backup thread
        self.auto_backup_thread = None
        self.auto_backup_active = False
        
    def load_backup_history(self):
        """Load backup history from file"""
        history_file = self.backup_dir / 'backup_history.json'
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                
                self.backup_history = []
                for item in history_data:
                    # Convert timestamp string back to datetime
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                    self.backup_history.append(BackupInfo(**item))
                
                self.logger.info(f"Loaded {len(self.backup_history)} backup records")
                
            except Exception as e:
                self.logger.error(f"Failed to load backup history: {str(e)}")
                self.backup_history = []
    
    def save_backup_history(self):
        """Save backup history to file"""
        history_file = self.backup_dir / 'backup_history.json'
        
        try:
            # Convert to serializable format
            history_data = []
            for backup in self.backup_history:
                backup_dict = asdict(backup)
                backup_dict['timestamp'] = backup.timestamp.isoformat()
                history_data.append(backup_dict)
            
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save backup history: {str(e)}")
    
    def create_backup_id(self) -> str:
        """Generate unique backup ID"""
        return f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def backup_faiss_index(self, backup_path: Path) -> bool:
        """Backup FAISS vector database"""
        try:
            vector_db_path = Path('data/ncert/vector_db')
            
            if not vector_db_path.exists():
                self.logger.warning("FAISS vector database not found - skipping")
                return True
            
            # Create FAISS backup directory
            faiss_backup_path = backup_path / 'faiss_index'
            faiss_backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy FAISS files
            faiss_files = [
                'faiss_index.bin',
                'chunk_metadata.json',
                'id_mapping.json'
            ]
            
            for file_name in faiss_files:
                source_file = vector_db_path / file_name
                if source_file.exists():
                    shutil.copy2(source_file, faiss_backup_path / file_name)
                    self.logger.debug(f"Backed up FAISS file: {file_name}")
            
            # Create FAISS metadata
            faiss_metadata = {
                'backup_timestamp': datetime.now().isoformat(),
                'vector_count': self._get_vector_count(),
                'index_size_bytes': sum(
                    (vector_db_path / f).stat().st_size 
                    for f in faiss_files 
                    if (vector_db_path / f).exists()
                )
            }
            
            with open(faiss_backup_path / 'faiss_metadata.json', 'w') as f:
                json.dump(faiss_metadata, f, indent=2)
            
            self.logger.info("FAISS index backup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"FAISS backup failed: {str(e)}")
            return False
    
    def backup_cache_data(self, backup_path: Path) -> bool:
        """Backup cached data"""
        try:
            cache_backup_path = backup_path / 'cache_data'
            cache_backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup session cache data
            try:
                from src.session.session_manager import session_manager
                
                # Export demo cache
                demo_cache = getattr(session_manager, 'demo_cache', {})
                if demo_cache:
                    with open(cache_backup_path / 'demo_cache.json', 'w') as f:
                        json.dump(demo_cache, f, indent=2)
                
                # Export demo questions
                demo_questions = getattr(session_manager, 'demo_questions', [])
                if demo_questions:
                    with open(cache_backup_path / 'demo_questions.json', 'w') as f:
                        json.dump(demo_questions, f, indent=2)
                
                self.logger.debug("Session cache data backed up")
                
            except Exception as e:
                self.logger.warning(f"Session cache backup failed: {str(e)}")
            
            # Backup performance metrics cache
            try:
                from src.utils.performance_tracker import performance_tracker
                
                metrics = performance_tracker.get_performance_summary()
                with open(cache_backup_path / 'performance_metrics.json', 'w') as f:
                    json.dump(metrics, f, indent=2, default=str)
                
                self.logger.debug("Performance metrics backed up")
                
            except Exception as e:
                self.logger.warning(f"Performance metrics backup failed: {str(e)}")
            
            # Backup audio cache (if exists)
            audio_storage_path = Path('audio_storage')
            if audio_storage_path.exists():
                audio_backup_path = cache_backup_path / 'audio_storage'
                shutil.copytree(audio_storage_path, audio_backup_path, dirs_exist_ok=True)
                self.logger.debug("Audio storage backed up")
            
            self.logger.info("Cache data backup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Cache backup failed: {str(e)}")
            return False
    
    def backup_system_config(self, backup_path: Path) -> bool:
        """Backup system configuration"""
        try:
            config_backup_path = backup_path / 'config'
            config_backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup configuration files
            config_files = [
                'config.py',
                '.env.example',
                'requirements.txt'
            ]
            
            for file_name in config_files:
                source_file = Path(file_name)
                if source_file.exists():
                    shutil.copy2(source_file, config_backup_path / file_name)
            
            # Create system state snapshot
            system_state = {
                'backup_timestamp': datetime.now().isoformat(),
                'environment': self.config.get_environment_config(),
                'deployment_info': self.config.get_deployment_info(),
                'python_version': os.sys.version,
                'platform': os.name
            }
            
            with open(config_backup_path / 'system_state.json', 'w') as f:
                json.dump(system_state, f, indent=2)
            
            self.logger.info("System configuration backup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"System config backup failed: {str(e)}")
            return False
    
    def create_backup(self, backup_type: str = 'full', components: List[str] = None) -> Optional[BackupInfo]:
        """Create system backup"""
        backup_id = self.create_backup_id()
        self.logger.info(f"Starting {backup_type} backup: {backup_id}")
        
        try:
            # Create backup directory
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Default components for full backup
            if components is None:
                if backup_type == 'full':
                    components = ['faiss', 'cache', 'config']
                elif backup_type == 'faiss_only':
                    components = ['faiss']
                elif backup_type == 'cache_only':
                    components = ['cache']
                else:
                    components = ['faiss', 'cache']
            
            # Perform backup operations
            success = True
            
            if 'faiss' in components:
                success &= self.backup_faiss_index(backup_path)
            
            if 'cache' in components:
                success &= self.backup_cache_data(backup_path)
            
            if 'config' in components:
                success &= self.backup_system_config(backup_path)
            
            if not success:
                self.logger.error(f"Backup {backup_id} failed")
                shutil.rmtree(backup_path, ignore_errors=True)
                return None
            
            # Create backup archive
            archive_path = self.backup_dir / f"{backup_id}.tar.gz"
            
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(backup_path, arcname=backup_id)
            
            # Remove temporary directory
            shutil.rmtree(backup_path)
            
            # Calculate backup size
            backup_size = archive_path.stat().st_size
            
            # Create backup info
            backup_info = BackupInfo(
                backup_id=backup_id,
                timestamp=datetime.now(),
                backup_type=backup_type,
                file_path=str(archive_path),
                size_bytes=backup_size,
                components=components,
                status='created',
                metadata={
                    'vector_count': self._get_vector_count() if 'faiss' in components else 0,
                    'environment': self.config.FLASK_ENV
                }
            )
            
            # Add to history
            self.backup_history.append(backup_info)
            self.save_backup_history()
            
            # Clean up old backups
            self.cleanup_old_backups()
            
            self.logger.info(f"Backup {backup_id} completed successfully ({backup_size / 1024 / 1024:.2f} MB)")
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            return None
    
    def restore_backup(self, backup_id: str, components: List[str] = None) -> bool:
        """Restore system from backup"""
        self.logger.info(f"Starting restore from backup: {backup_id}")
        
        try:
            # Find backup info
            backup_info = None
            for backup in self.backup_history:
                if backup.backup_id == backup_id:
                    backup_info = backup
                    break
            
            if not backup_info:
                self.logger.error(f"Backup {backup_id} not found in history")
                return False
            
            # Check if backup file exists
            backup_file = Path(backup_info.file_path)
            if not backup_file.exists():
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Extract backup
            restore_path = self.backup_dir / f"restore_{backup_id}"
            restore_path.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(restore_path)
            
            backup_content_path = restore_path / backup_id
            
            # Default to all available components
            if components is None:
                components = backup_info.components
            
            # Restore components
            success = True
            
            if 'faiss' in components and 'faiss' in backup_info.components:
                success &= self._restore_faiss_index(backup_content_path)
            
            if 'cache' in components and 'cache' in backup_info.components:
                success &= self._restore_cache_data(backup_content_path)
            
            if 'config' in components and 'config' in backup_info.components:
                success &= self._restore_system_config(backup_content_path)
            
            # Clean up restore directory
            shutil.rmtree(restore_path, ignore_errors=True)
            
            if success:
                backup_info.status = 'restored'
                self.save_backup_history()
                self.logger.info(f"Restore from backup {backup_id} completed successfully")
            else:
                self.logger.error(f"Restore from backup {backup_id} failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Restore failed: {str(e)}")
            return False
    
    def _restore_faiss_index(self, backup_path: Path) -> bool:
        """Restore FAISS vector database"""
        try:
            faiss_backup_path = backup_path / 'faiss_index'
            
            if not faiss_backup_path.exists():
                self.logger.warning("No FAISS data in backup")
                return True
            
            # Create target directory
            vector_db_path = Path('data/ncert/vector_db')
            vector_db_path.mkdir(parents=True, exist_ok=True)
            
            # Restore FAISS files
            faiss_files = [
                'faiss_index.bin',
                'chunk_metadata.json',
                'id_mapping.json'
            ]
            
            for file_name in faiss_files:
                source_file = faiss_backup_path / file_name
                if source_file.exists():
                    shutil.copy2(source_file, vector_db_path / file_name)
                    self.logger.debug(f"Restored FAISS file: {file_name}")
            
            self.logger.info("FAISS index restore completed")
            return True
            
        except Exception as e:
            self.logger.error(f"FAISS restore failed: {str(e)}")
            return False
    
    def _restore_cache_data(self, backup_path: Path) -> bool:
        """Restore cached data"""
        try:
            cache_backup_path = backup_path / 'cache_data'
            
            if not cache_backup_path.exists():
                self.logger.warning("No cache data in backup")
                return True
            
            # Restore session cache
            try:
                from src.session.session_manager import session_manager
                
                # Restore demo cache
                demo_cache_file = cache_backup_path / 'demo_cache.json'
                if demo_cache_file.exists():
                    with open(demo_cache_file, 'r') as f:
                        demo_cache = json.load(f)
                    session_manager.demo_cache = demo_cache
                
                # Restore demo questions
                demo_questions_file = cache_backup_path / 'demo_questions.json'
                if demo_questions_file.exists():
                    with open(demo_questions_file, 'r') as f:
                        demo_questions = json.load(f)
                    session_manager.demo_questions = demo_questions
                
                self.logger.debug("Session cache data restored")
                
            except Exception as e:
                self.logger.warning(f"Session cache restore failed: {str(e)}")
            
            # Restore audio storage
            audio_backup_path = cache_backup_path / 'audio_storage'
            if audio_backup_path.exists():
                audio_storage_path = Path('audio_storage')
                if audio_storage_path.exists():
                    shutil.rmtree(audio_storage_path)
                shutil.copytree(audio_backup_path, audio_storage_path)
                self.logger.debug("Audio storage restored")
            
            self.logger.info("Cache data restore completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Cache restore failed: {str(e)}")
            return False
    
    def _restore_system_config(self, backup_path: Path) -> bool:
        """Restore system configuration (informational only)"""
        try:
            config_backup_path = backup_path / 'config'
            
            if not config_backup_path.exists():
                self.logger.warning("No config data in backup")
                return True
            
            # Read system state for comparison
            system_state_file = config_backup_path / 'system_state.json'
            if system_state_file.exists():
                with open(system_state_file, 'r') as f:
                    backup_state = json.load(f)
                
                self.logger.info(f"Backup was created in environment: {backup_state.get('environment', {}).get('environment', 'unknown')}")
                self.logger.info(f"Current environment: {self.config.FLASK_ENV}")
            
            self.logger.info("System configuration restore completed (informational only)")
            return True
            
        except Exception as e:
            self.logger.error(f"System config restore failed: {str(e)}")
            return False
    
    def _get_vector_count(self) -> int:
        """Get current vector count from FAISS index"""
        try:
            import faiss
            vector_db_path = Path('data/ncert/vector_db/faiss_index.bin')
            
            if not vector_db_path.exists():
                return 0
            
            index = faiss.read_index(str(vector_db_path))
            return index.ntotal
            
        except Exception:
            return 0
    
    def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        try:
            # Remove backups older than retention period
            cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
            
            backups_to_remove = []
            for backup in self.backup_history:
                if backup.timestamp < cutoff_date:
                    backups_to_remove.append(backup)
            
            # Keep at least one backup
            if len(self.backup_history) - len(backups_to_remove) < 1:
                backups_to_remove = backups_to_remove[:-1]
            
            # Remove old backups
            for backup in backups_to_remove:
                try:
                    backup_file = Path(backup.file_path)
                    if backup_file.exists():
                        backup_file.unlink()
                    
                    self.backup_history.remove(backup)
                    self.logger.info(f"Removed old backup: {backup.backup_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to remove backup {backup.backup_id}: {str(e)}")
            
            # Limit total number of backups
            if len(self.backup_history) > self.max_backups:
                excess_backups = sorted(self.backup_history, key=lambda b: b.timestamp)[:-self.max_backups]
                
                for backup in excess_backups:
                    try:
                        backup_file = Path(backup.file_path)
                        if backup_file.exists():
                            backup_file.unlink()
                        
                        self.backup_history.remove(backup)
                        self.logger.info(f"Removed excess backup: {backup.backup_id}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to remove excess backup {backup.backup_id}: {str(e)}")
            
            self.save_backup_history()
            
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {str(e)}")
    
    def start_auto_backup(self):
        """Start automatic backup process"""
        if not self.auto_backup_enabled:
            self.logger.info("Auto-backup is disabled")
            return
        
        if self.auto_backup_active:
            self.logger.warning("Auto-backup already active")
            return
        
        self.auto_backup_active = True
        self.logger.info(f"Starting auto-backup (interval: {self.auto_backup_interval}h)")
        
        def auto_backup_loop():
            while self.auto_backup_active:
                try:
                    # Wait for the interval
                    time.sleep(self.auto_backup_interval * 3600)  # Convert hours to seconds
                    
                    if self.auto_backup_active:
                        self.logger.info("Performing automatic backup")
                        backup_info = self.create_backup('incremental', ['faiss', 'cache'])
                        
                        if backup_info:
                            self.logger.info(f"Auto-backup completed: {backup_info.backup_id}")
                        else:
                            self.logger.error("Auto-backup failed")
                    
                except Exception as e:
                    self.logger.error(f"Auto-backup error: {str(e)}")
                    time.sleep(300)  # Wait 5 minutes before retrying
        
        self.auto_backup_thread = threading.Thread(target=auto_backup_loop, daemon=True)
        self.auto_backup_thread.start()
    
    def stop_auto_backup(self):
        """Stop automatic backup process"""
        self.auto_backup_active = False
        self.logger.info("Auto-backup stopped")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get backup system status"""
        return {
            'auto_backup_enabled': self.auto_backup_enabled,
            'auto_backup_active': self.auto_backup_active,
            'backup_count': len(self.backup_history),
            'latest_backup': self.backup_history[-1].backup_id if self.backup_history else None,
            'latest_backup_timestamp': self.backup_history[-1].timestamp.isoformat() if self.backup_history else None,
            'total_backup_size_mb': sum(b.size_bytes for b in self.backup_history) / 1024 / 1024,
            'retention_days': self.backup_retention_days,
            'max_backups': self.max_backups
        }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        return [
            {
                'backup_id': backup.backup_id,
                'timestamp': backup.timestamp.isoformat(),
                'backup_type': backup.backup_type,
                'size_mb': backup.size_bytes / 1024 / 1024,
                'components': backup.components,
                'status': backup.status,
                'metadata': backup.metadata
            }
            for backup in sorted(self.backup_history, key=lambda b: b.timestamp, reverse=True)
        ]

# Global backup manager instance
backup_manager = None

def get_backup_manager(config):
    """Get or create global backup manager instance"""
    global backup_manager
    if backup_manager is None:
        backup_manager = BackupManager(config)
    return backup_manager