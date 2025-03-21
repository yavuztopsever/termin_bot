"""
Pattern Analyzer implementation for detecting bot behavior and patterns.
"""

from typing import Dict, Any, List, Optional
import time
from .behavior_analyzer import BehaviorAnalyzer
from .anomaly_detector import AnomalyDetector
from ...utils.logger import get_logger
from ...config import settings

logger = get_logger(__name__)

class PatternAnalyzer:
    """Pattern Analyzer for detecting bot behavior and patterns."""
    
    def __init__(
        self,
        request_threshold: int = 100,
        time_window: int = 3600,
        anomaly_threshold: float = 0.8
    ):
        """Initialize the Pattern Analyzer."""
        self.request_threshold = request_threshold
        self.time_window = time_window
        self.anomaly_threshold = anomaly_threshold
        
        self.behavior_analyzer = BehaviorAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.request_history: Dict[str, List[float]] = {}
        
    async def start(self):
        """Start the Pattern Analyzer."""
        await self.behavior_analyzer.start()
        await self.anomaly_detector.start()
        
    async def stop(self):
        """Stop the Pattern Analyzer."""
        await self.behavior_analyzer.stop()
        await self.anomaly_detector.stop()
        
    async def analyze_request(
        self,
        client_id: str,
        request_data: Dict[str, Any]
    ) -> bool:
        """Analyze a request for bot behavior."""
        try:
            # Update request history
            current_time = time.time()
            if client_id not in self.request_history:
                self.request_history[client_id] = []
                
            self.request_history[client_id].append(current_time)
            
            # Clean old requests
            self._clean_old_requests(client_id)
            
            # Check request frequency
            if len(self.request_history[client_id]) > self.request_threshold:
                logger.warning(
                    f"Client {client_id} exceeded request threshold"
                )
                return False
                
            # Analyze behavior
            behavior_score = await self.behavior_analyzer.analyze(
                client_id,
                request_data
            )
            
            if behavior_score > self.anomaly_threshold:
                logger.warning(
                    f"Client {client_id} detected as bot "
                    f"(behavior score: {behavior_score})"
                )
                return False
                
            # Detect anomalies
            anomaly_score = await self.anomaly_detector.detect(
                client_id,
                request_data
            )
            
            if anomaly_score > self.anomaly_threshold:
                logger.warning(
                    f"Client {client_id} detected as anomalous "
                    f"(anomaly score: {anomaly_score})"
                )
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error analyzing request: {str(e)}")
            return False
            
    def _clean_old_requests(self, client_id: str):
        """Clean old requests from history."""
        try:
            current_time = time.time()
            self.request_history[client_id] = [
                t for t in self.request_history[client_id]
                if current_time - t <= self.time_window
            ]
            
        except Exception as e:
            logger.error(f"Error cleaning old requests: {str(e)}")
            
    async def get_analysis_info(self, client_id: str) -> Dict[str, Any]:
        """Get analysis information for client."""
        try:
            return {
                "request_count": len(self.request_history.get(client_id, [])),
                "request_threshold": self.request_threshold,
                "time_window": self.time_window,
                "behavior_score": await self.behavior_analyzer.get_score(client_id),
                "anomaly_score": await self.anomaly_detector.get_score(client_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis info: {str(e)}")
            return {}
            
    async def reset_analysis(self, client_id: str):
        """Reset analysis for client."""
        try:
            if client_id in self.request_history:
                del self.request_history[client_id]
                
            await self.behavior_analyzer.reset(client_id)
            await self.anomaly_detector.reset(client_id)
            
        except Exception as e:
            logger.error(f"Error resetting analysis: {str(e)}")
            
    async def update_thresholds(
        self,
        request_threshold: Optional[int] = None,
        time_window: Optional[int] = None,
        anomaly_threshold: Optional[float] = None
    ):
        """Update analysis thresholds."""
        try:
            if request_threshold is not None:
                self.request_threshold = request_threshold
                
            if time_window is not None:
                self.time_window = time_window
                
            if anomaly_threshold is not None:
                self.anomaly_threshold = anomaly_threshold
                
        except Exception as e:
            logger.error(f"Error updating thresholds: {str(e)}") 