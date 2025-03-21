"""
Anomaly Detector implementation for detecting anomalous behavior patterns.
"""

from typing import Dict, Any, List, Optional
import time
import numpy as np
from sklearn.ensemble import IsolationForest
from ...utils.logger import get_logger
from ...config import settings

logger = get_logger(__name__)

class AnomalyDetector:
    """Anomaly Detector for detecting anomalous behavior patterns."""
    
    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        max_samples: int = 1000,
        window_size: int = 100
    ):
        """Initialize the Anomaly Detector."""
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.window_size = window_size
        
        self.models: Dict[str, IsolationForest] = {}
        self.features: Dict[str, List[Dict[str, float]]] = {}
        self.scores: Dict[str, float] = {}
        
    async def start(self):
        """Start the Anomaly Detector."""
        # Initialize any required resources
        pass
        
    async def stop(self):
        """Stop the Anomaly Detector."""
        # Clean up resources
        pass
        
    async def detect(
        self,
        client_id: str,
        request_data: Dict[str, Any]
    ) -> float:
        """Detect anomalies in client behavior and return a score."""
        try:
            # Extract features
            features = self._extract_features(request_data)
            
            # Get or create client model
            if client_id not in self.models:
                self.models[client_id] = IsolationForest(
                    contamination=self.contamination,
                    n_estimators=self.n_estimators,
                    max_samples=self.max_samples,
                    random_state=42
                )
                self.features[client_id] = []
                
            # Update features
            self.features[client_id].append(features)
            
            # Maintain window size
            if len(self.features[client_id]) > self.window_size:
                self.features[client_id] = self.features[client_id][-self.window_size:]
                
            # Train model if enough samples
            if len(self.features[client_id]) >= self.window_size:
                X = np.array([
                    list(f.values()) for f in self.features[client_id]
                ])
                self.models[client_id].fit(X)
                
            # Calculate anomaly score
            if len(self.features[client_id]) > 0:
                X = np.array([list(features.values())])
                score = -self.models[client_id].score_samples(X)[0]
                score = (score - self.models[client_id].offset_) / self.models[client_id].contamination_
                score = min(1.0, max(0.0, score))
            else:
                score = 0.0
                
            # Update client score
            self.scores[client_id] = score
            
            return score
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return 1.0  # Return high score on error
            
    def _extract_features(self, request_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract features for anomaly detection."""
        try:
            features = {}
            
            # Extract timing features
            if "timestamp" in request_data:
                features["hour"] = time.localtime(request_data["timestamp"]).tm_hour
                features["minute"] = time.localtime(request_data["timestamp"]).tm_min
                features["second"] = time.localtime(request_data["timestamp"]).tm_sec
                
            # Extract request features
            if "method" in request_data:
                features["method"] = hash(request_data["method"]) % 10
                
            if "path" in request_data:
                features["path_length"] = len(request_data["path"])
                features["path_depth"] = request_data["path"].count("/")
                features["path_entropy"] = self._calculate_entropy(request_data["path"])
                
            if "headers" in request_data:
                features["header_count"] = len(request_data["headers"])
                features["header_entropy"] = self._calculate_entropy(
                    str(request_data["headers"])
                )
                
            if "body" in request_data:
                body_str = str(request_data["body"])
                features["body_size"] = len(body_str)
                features["body_entropy"] = self._calculate_entropy(body_str)
                
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            return {}
            
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text."""
        try:
            if not text:
                return 0.0
                
            # Count character frequencies
            freq = {}
            for char in text:
                freq[char] = freq.get(char, 0) + 1
                
            # Calculate probabilities
            probs = [count / len(text) for count in freq.values()]
            
            # Calculate entropy
            entropy = -sum(p * np.log2(p) for p in probs)
            
            return entropy
            
        except Exception as e:
            logger.error(f"Error calculating entropy: {str(e)}")
            return 0.0
            
    async def get_score(self, client_id: str) -> float:
        """Get current anomaly score for client."""
        return self.scores.get(client_id, 0.0)
        
    async def reset(self, client_id: str):
        """Reset anomaly detection for client."""
        try:
            if client_id in self.models:
                del self.models[client_id]
                
            if client_id in self.features:
                del self.features[client_id]
                
            if client_id in self.scores:
                del self.scores[client_id]
                
        except Exception as e:
            logger.error(f"Error resetting anomaly detection: {str(e)}")
            
    async def update_thresholds(
        self,
        contamination: Optional[float] = None,
        n_estimators: Optional[int] = None,
        max_samples: Optional[int] = None,
        window_size: Optional[int] = None
    ):
        """Update detection thresholds."""
        try:
            if contamination is not None:
                self.contamination = contamination
                
            if n_estimators is not None:
                self.n_estimators = n_estimators
                
            if max_samples is not None:
                self.max_samples = max_samples
                
            if window_size is not None:
                self.window_size = window_size
                
        except Exception as e:
            logger.error(f"Error updating thresholds: {str(e)}") 