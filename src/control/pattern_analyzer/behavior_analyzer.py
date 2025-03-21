"""
Behavior Analyzer implementation for analyzing client behavior patterns.
"""

from typing import Dict, Any, Optional
import time
from ...utils.logger import get_logger
from ...config import settings

logger = get_logger(__name__)

class BehaviorAnalyzer:
    """Behavior Analyzer for analyzing client behavior patterns."""
    
    def __init__(
        self,
        pattern_threshold: float = 0.7,
        learning_rate: float = 0.1,
        max_patterns: int = 1000
    ):
        """Initialize the Behavior Analyzer."""
        self.pattern_threshold = pattern_threshold
        self.learning_rate = learning_rate
        self.max_patterns = max_patterns
        
        self.patterns: Dict[str, Dict[str, Any]] = {}
        self.scores: Dict[str, float] = {}
        
    async def start(self):
        """Start the Behavior Analyzer."""
        # Initialize any required resources
        pass
        
    async def stop(self):
        """Stop the Behavior Analyzer."""
        # Clean up resources
        pass
        
    async def analyze(
        self,
        client_id: str,
        request_data: Dict[str, Any]
    ) -> float:
        """Analyze client behavior and return a score."""
        try:
            # Extract behavior features
            features = self._extract_features(request_data)
            
            # Get or create client patterns
            if client_id not in self.patterns:
                self.patterns[client_id] = {
                    "features": {},
                    "count": 0,
                    "last_update": time.time()
                }
                
            # Update patterns
            self._update_patterns(client_id, features)
            
            # Calculate behavior score
            score = self._calculate_score(client_id, features)
            
            # Update client score
            self.scores[client_id] = score
            
            return score
            
        except Exception as e:
            logger.error(f"Error analyzing behavior: {str(e)}")
            return 1.0  # Return high score on error
            
    def _extract_features(self, request_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract behavior features from request data."""
        try:
            features = {}
            
            # Extract timing features
            if "timestamp" in request_data:
                features["hour"] = time.localtime(request_data["timestamp"]).tm_hour
                features["minute"] = time.localtime(request_data["timestamp"]).tm_min
                
            # Extract request features
            if "method" in request_data:
                features["method"] = hash(request_data["method"]) % 10
                
            if "path" in request_data:
                features["path_length"] = len(request_data["path"])
                features["path_depth"] = request_data["path"].count("/")
                
            if "headers" in request_data:
                features["header_count"] = len(request_data["headers"])
                
            if "body" in request_data:
                features["body_size"] = len(str(request_data["body"]))
                
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            return {}
            
    def _update_patterns(
        self,
        client_id: str,
        features: Dict[str, float]
    ):
        """Update client behavior patterns."""
        try:
            patterns = self.patterns[client_id]
            
            # Update feature patterns
            for feature, value in features.items():
                if feature not in patterns["features"]:
                    patterns["features"][feature] = {
                        "mean": value,
                        "std": 0.0,
                        "count": 1
                    }
                else:
                    # Update mean and standard deviation
                    old_mean = patterns["features"][feature]["mean"]
                    old_std = patterns["features"][feature]["std"]
                    old_count = patterns["features"][feature]["count"]
                    
                    new_count = old_count + 1
                    new_mean = old_mean + (value - old_mean) / new_count
                    new_std = (
                        (old_std ** 2 * old_count + (value - new_mean) ** 2) /
                        new_count
                    ) ** 0.5
                    
                    patterns["features"][feature].update({
                        "mean": new_mean,
                        "std": new_std,
                        "count": new_count
                    })
                    
            # Update pattern count and timestamp
            patterns["count"] += 1
            patterns["last_update"] = time.time()
            
            # Limit pattern count
            if patterns["count"] > self.max_patterns:
                self._prune_patterns(client_id)
                
        except Exception as e:
            logger.error(f"Error updating patterns: {str(e)}")
            
    def _calculate_score(
        self,
        client_id: str,
        features: Dict[str, float]
    ) -> float:
        """Calculate behavior score based on patterns."""
        try:
            patterns = self.patterns[client_id]
            score = 0.0
            weight = 0.0
            
            for feature, value in features.items():
                if feature in patterns["features"]:
                    pattern = patterns["features"][feature]
                    
                    # Calculate z-score
                    if pattern["std"] > 0:
                        z_score = abs(value - pattern["mean"]) / pattern["std"]
                        feature_score = min(1.0, z_score / 3.0)  # Cap at 3 standard deviations
                        
                        # Weight by feature count
                        feature_weight = min(1.0, pattern["count"] / self.max_patterns)
                        
                        score += feature_score * feature_weight
                        weight += feature_weight
                        
            # Normalize score
            if weight > 0:
                score /= weight
                
            return score
            
        except Exception as e:
            logger.error(f"Error calculating score: {str(e)}")
            return 1.0
            
    def _prune_patterns(self, client_id: str):
        """Prune old patterns to maintain size limit."""
        try:
            patterns = self.patterns[client_id]
            
            # Keep only the most recent patterns
            if patterns["count"] > self.max_patterns:
                patterns["count"] = self.max_patterns
                
                # Reset feature statistics
                for feature in patterns["features"]:
                    patterns["features"][feature]["count"] = self.max_patterns
                    
        except Exception as e:
            logger.error(f"Error pruning patterns: {str(e)}")
            
    async def get_score(self, client_id: str) -> float:
        """Get current behavior score for client."""
        return self.scores.get(client_id, 0.0)
        
    async def reset(self, client_id: str):
        """Reset behavior analysis for client."""
        try:
            if client_id in self.patterns:
                del self.patterns[client_id]
                
            if client_id in self.scores:
                del self.scores[client_id]
                
        except Exception as e:
            logger.error(f"Error resetting behavior analysis: {str(e)}")
            
    async def update_thresholds(
        self,
        pattern_threshold: Optional[float] = None,
        learning_rate: Optional[float] = None,
        max_patterns: Optional[int] = None
    ):
        """Update analysis thresholds."""
        try:
            if pattern_threshold is not None:
                self.pattern_threshold = pattern_threshold
                
            if learning_rate is not None:
                self.learning_rate = learning_rate
                
            if max_patterns is not None:
                self.max_patterns = max_patterns
                
        except Exception as e:
            logger.error(f"Error updating thresholds: {str(e)}") 