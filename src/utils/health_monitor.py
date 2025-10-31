"""
Health monitoring and system restart capabilities for VidyaVani IVR Learning System
"""

import os
import time
import logging
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class HealthCheckResult:
    """Health check result data structure"""
    component: str
    status: str  # healthy, warning, critical
    response_time: float
    message: str
    timestamp: datetime
    details: Dict[str, Any] = None

@dataclass
class SystemHealth:
    """Overall system health status"""
    overall_status: str
    healthy_components: int
    warning_components: int
    critical_components: int
    last_check: datetime
    checks: List[HealthCheckResult]

class HealthMonitor:
    """Automated health monitoring and restart system"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.health_history: List[SystemHealth] = []
        self.restart_count = 0
        self.last_restart = None
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Health check thresholds
        self.response_time_threshold = 5.0  # seconds
        self.memory_threshold = 80  # percentage
        self.disk_threshold = 90  # percentage
        self.consecutive_failures_threshold = 3
        
        # Restart policy
        self.max_restarts_per_hour = 3
        self.restart_cooldown = 300  # 5 minutes
        
    def check_api_health(self) -> HealthCheckResult:
        """Check health of external APIs"""
        start_time = time.time()
        
        # Skip OpenAI check if using Gemini
        if self.config.USE_GEMINI:
            return HealthCheckResult(
                component="ai_api",
                status="healthy",
                response_time=0.0,
                message="Using Gemini API (OpenAI check skipped)",
                timestamp=datetime.now()
            )
        
        try:
            # Test OpenAI API
            import openai
            openai.api_key = self.config.OPENAI_API_KEY
            
            # Simple API test
            response = openai.models.list()
            
            response_time = time.time() - start_time
            
            if response_time > self.response_time_threshold:
                return HealthCheckResult(
                    component="openai_api",
                    status="warning",
                    response_time=response_time,
                    message=f"OpenAI API slow response: {response_time:.2f}s",
                    timestamp=datetime.now()
                )
            
            return HealthCheckResult(
                component="openai_api",
                status="healthy",
                response_time=response_time,
                message="OpenAI API responding normally",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="openai_api",
                status="critical",
                response_time=time.time() - start_time,
                message=f"OpenAI API error: {str(e)}",
                timestamp=datetime.now()
            )
    
    def check_google_cloud_health(self) -> HealthCheckResult:
        """Check Google Cloud services health"""
        start_time = time.time()
        
        try:
            # Test Google Cloud credentials
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not credentials_path or not os.path.exists(credentials_path):
                return HealthCheckResult(
                    component="google_cloud",
                    status="warning",
                    response_time=time.time() - start_time,
                    message="Google Cloud credentials not found",
                    timestamp=datetime.now()
                )
            
            # Test Speech-to-Text API
            from google.cloud import speech
            client = speech.SpeechClient()
            
            response_time = time.time() - start_time
            
            return HealthCheckResult(
                component="google_cloud",
                status="healthy",
                response_time=response_time,
                message="Google Cloud services accessible",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="google_cloud",
                status="critical",
                response_time=time.time() - start_time,
                message=f"Google Cloud error: {str(e)}",
                timestamp=datetime.now()
            )
    
    def check_vector_database_health(self) -> HealthCheckResult:
        """Check FAISS vector database health"""
        start_time = time.time()
        
        try:
            vector_db_path = Path('data/ncert/vector_db')
            
            # Check if vector database files exist
            required_files = ['faiss_index.bin', 'chunk_metadata.json', 'id_mapping.json']
            missing_files = []
            
            for file_name in required_files:
                if not (vector_db_path / file_name).exists():
                    missing_files.append(file_name)
            
            response_time = time.time() - start_time
            
            if missing_files:
                return HealthCheckResult(
                    component="vector_database",
                    status="warning",
                    response_time=response_time,
                    message=f"Missing vector DB files: {', '.join(missing_files)}",
                    timestamp=datetime.now()
                )
            
            # Test FAISS index loading
            import faiss
            import numpy as np
            
            index = faiss.read_index(str(vector_db_path / 'faiss_index.bin'))
            
            return HealthCheckResult(
                component="vector_database",
                status="healthy",
                response_time=response_time,
                message=f"Vector database healthy ({index.ntotal} vectors)",
                timestamp=datetime.now(),
                details={"vector_count": index.ntotal}
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="vector_database",
                status="critical",
                response_time=time.time() - start_time,
                message=f"Vector database error: {str(e)}",
                timestamp=datetime.now()
            )
    
    def check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage"""
        start_time = time.time()
        
        try:
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            response_time = time.time() - start_time
            
            details = {
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "cpu_percent": cpu_percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_free_gb": disk.free / (1024**3)
            }
            
            # Determine status
            if memory_percent > self.memory_threshold or disk_percent > self.disk_threshold:
                status = "critical"
                message = f"High resource usage - Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%"
            elif memory_percent > (self.memory_threshold - 10) or disk_percent > (self.disk_threshold - 10):
                status = "warning"
                message = f"Moderate resource usage - Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%"
            else:
                status = "healthy"
                message = f"Resource usage normal - Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%"
            
            return HealthCheckResult(
                component="system_resources",
                status=status,
                response_time=response_time,
                message=message,
                timestamp=datetime.now(),
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="system_resources",
                status="warning",
                response_time=time.time() - start_time,
                message=f"Could not check system resources: {str(e)}",
                timestamp=datetime.now()
            )
    
    def check_redis_health(self) -> Optional[HealthCheckResult]:
        """Check Redis health if enabled"""
        if not self.config.USE_REDIS:
            return None
        
        start_time = time.time()
        
        try:
            import redis
            r = redis.from_url(self.config.REDIS_URL)
            
            # Test Redis connection
            r.ping()
            
            # Get Redis info
            info = r.info()
            
            response_time = time.time() - start_time
            
            return HealthCheckResult(
                component="redis",
                status="healthy",
                response_time=response_time,
                message="Redis connection healthy",
                timestamp=datetime.now(),
                details={
                    "connected_clients": info.get('connected_clients', 0),
                    "used_memory_human": info.get('used_memory_human', 'unknown'),
                    "uptime_in_seconds": info.get('uptime_in_seconds', 0)
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="redis",
                status="warning",
                response_time=time.time() - start_time,
                message=f"Redis unavailable (optional): {str(e)}",
                timestamp=datetime.now()
            )
    
    def perform_health_check(self) -> SystemHealth:
        """Perform comprehensive health check"""
        self.logger.info("Performing health check...")
        
        checks = []
        
        # Run all health checks
        checks.append(self.check_api_health())
        checks.append(self.check_google_cloud_health())
        checks.append(self.check_vector_database_health())
        checks.append(self.check_system_resources())
        
        redis_check = self.check_redis_health()
        if redis_check:
            checks.append(redis_check)
        
        # Calculate overall health
        healthy_count = sum(1 for check in checks if check.status == "healthy")
        warning_count = sum(1 for check in checks if check.status == "warning")
        critical_count = sum(1 for check in checks if check.status == "critical")
        
        # Determine overall status
        if critical_count > 0:
            overall_status = "critical"
        elif warning_count > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        system_health = SystemHealth(
            overall_status=overall_status,
            healthy_components=healthy_count,
            warning_components=warning_count,
            critical_components=critical_count,
            last_check=datetime.now(),
            checks=checks
        )
        
        # Store in history
        self.health_history.append(system_health)
        
        # Keep only last 100 health checks
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]
        
        self.logger.info(f"Health check completed - Status: {overall_status}")
        
        return system_health
    
    def should_restart(self, health: SystemHealth) -> bool:
        """Determine if system should be restarted"""
        # Check if we've exceeded restart limits
        if self.last_restart:
            time_since_restart = datetime.now() - self.last_restart
            if time_since_restart.total_seconds() < self.restart_cooldown:
                self.logger.info(f"Restart cooldown active ({self.restart_cooldown - time_since_restart.total_seconds():.0f}s remaining)")
                return False
        
        # Check restart rate limit
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_restarts = sum(1 for h in self.health_history 
                            if h.last_check > one_hour_ago and 
                            any(check.message.startswith("System restart") for check in h.checks))
        
        if recent_restarts >= self.max_restarts_per_hour:
            self.logger.warning(f"Restart rate limit exceeded ({recent_restarts}/{self.max_restarts_per_hour} per hour)")
            return False
        
        # Check for critical failures
        critical_components = [check.component for check in health.checks if check.status == "critical"]
        
        if critical_components:
            self.logger.warning(f"Critical components detected: {', '.join(critical_components)}")
            
            # Check for consecutive failures
            if len(self.health_history) >= self.consecutive_failures_threshold:
                recent_checks = self.health_history[-self.consecutive_failures_threshold:]
                all_critical = all(h.critical_components > 0 for h in recent_checks)
                
                if all_critical:
                    self.logger.error("Consecutive critical failures detected - restart required")
                    return True
        
        return False
    
    def restart_system(self) -> bool:
        """Restart the system"""
        self.logger.warning("Initiating system restart...")
        
        try:
            self.restart_count += 1
            self.last_restart = datetime.now()
            
            # Log restart attempt
            restart_check = HealthCheckResult(
                component="system_restart",
                status="warning",
                response_time=0,
                message=f"System restart initiated (attempt #{self.restart_count})",
                timestamp=datetime.now(),
                details={"restart_count": self.restart_count}
            )
            
            # Add to current health status
            if self.health_history:
                self.health_history[-1].checks.append(restart_check)
            
            # Different restart methods based on deployment platform
            platform = self.config.DEPLOYMENT_PLATFORM
            
            if platform == 'render':
                # Render.com - exit with error code to trigger restart
                self.logger.info("Triggering Render.com restart...")
                os._exit(1)
                
            elif platform == 'railway':
                # Railway.app - exit with error code to trigger restart
                self.logger.info("Triggering Railway.app restart...")
                os._exit(1)
                
            elif platform == 'docker':
                # Docker - exit with error code, let Docker restart policy handle it
                self.logger.info("Triggering Docker restart...")
                os._exit(1)
                
            else:
                # Local/other - try to restart gunicorn process
                self.logger.info("Attempting local process restart...")
                
                # Get current process PID
                pid = os.getpid()
                
                # Send SIGTERM to current process
                os.kill(pid, 15)  # SIGTERM
                
                return True
                
        except Exception as e:
            self.logger.error(f"System restart failed: {str(e)}")
            return False
    
    def start_monitoring(self, interval: int = 60):
        """Start automated health monitoring"""
        if self.monitoring_active:
            self.logger.warning("Health monitoring already active")
            return
        
        self.monitoring_active = True
        self.logger.info(f"Starting health monitoring (interval: {interval}s)")
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    # Perform health check
                    health = self.perform_health_check()
                    
                    # Check if restart is needed
                    if self.should_restart(health):
                        self.restart_system()
                        break  # Exit monitoring loop after restart
                    
                    # Wait for next check
                    time.sleep(interval)
                    
                except Exception as e:
                    self.logger.error(f"Health monitoring error: {str(e)}")
                    time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop automated health monitoring"""
        self.monitoring_active = False
        self.logger.info("Health monitoring stopped")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        if not self.health_history:
            return {"status": "unknown", "message": "No health checks performed yet"}
        
        latest_health = self.health_history[-1]
        
        return {
            "overall_status": latest_health.overall_status,
            "last_check": latest_health.last_check.isoformat(),
            "components": {
                "healthy": latest_health.healthy_components,
                "warning": latest_health.warning_components,
                "critical": latest_health.critical_components
            },
            "checks": [asdict(check) for check in latest_health.checks],
            "restart_info": {
                "restart_count": self.restart_count,
                "last_restart": self.last_restart.isoformat() if self.last_restart else None,
                "monitoring_active": self.monitoring_active
            }
        }
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_history = [
            asdict(health) for health in self.health_history
            if health.last_check > cutoff_time
        ]
        
        return recent_history

# Global health monitor instance
health_monitor = None

def get_health_monitor(config):
    """Get or create global health monitor instance"""
    global health_monitor
    if health_monitor is None:
        health_monitor = HealthMonitor(config)
    return health_monitor