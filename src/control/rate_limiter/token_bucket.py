"""
Token Bucket implementation for rate limiting.
"""

from typing import Dict, Any
import time
from ...utils.logger import get_logger

logger = get_logger(__name__)

class TokenBucket:
    """Token Bucket implementation for rate limiting."""
    
    def __init__(self, rate: float = 1.0, burst: int = 10):
        """Initialize the Token Bucket."""
        self.rate = rate  # tokens per second
        self.burst = burst
        self.tokens: Dict[str, float] = {}
        self.last_update: Dict[str, float] = {}
        
    def acquire(self, client_id: str) -> bool:
        """Acquire a token for the client."""
        try:
            current_time = time.time()
            
            # Initialize client if not exists
            if client_id not in self.tokens:
                self.tokens[client_id] = self.burst
                self.last_update[client_id] = current_time
                return True
                
            # Calculate tokens to add
            time_passed = current_time - self.last_update[client_id]
            tokens_to_add = time_passed * self.rate
            
            # Update tokens
            self.tokens[client_id] = min(
                self.burst,
                self.tokens[client_id] + tokens_to_add
            )
            self.last_update[client_id] = current_time
            
            # Check if token available
            if self.tokens[client_id] >= 1:
                self.tokens[client_id] -= 1
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error acquiring token: {str(e)}")
            return False
            
    def get_remaining_tokens(self, client_id: str) -> float:
        """Get remaining tokens for client."""
        try:
            if client_id not in self.tokens:
                return self.burst
                
            current_time = time.time()
            time_passed = current_time - self.last_update[client_id]
            tokens_to_add = time_passed * self.rate
            
            return min(
                self.burst,
                self.tokens[client_id] + tokens_to_add
            )
            
        except Exception as e:
            logger.error(f"Error getting remaining tokens: {str(e)}")
            return 0.0
            
    def reset_tokens(self, client_id: str):
        """Reset tokens for client."""
        try:
            if client_id in self.tokens:
                self.tokens[client_id] = self.burst
                self.last_update[client_id] = time.time()
                
        except Exception as e:
            logger.error(f"Error resetting tokens: {str(e)}")
            
    def update_rate(self, rate: float = None, burst: int = None):
        """Update rate and burst size."""
        try:
            if rate is not None:
                self.rate = rate
                
            if burst is not None:
                self.burst = burst
                # Reset all clients to new burst size
                for client_id in self.tokens:
                    self.tokens[client_id] = burst
                    
        except Exception as e:
            logger.error(f"Error updating rate: {str(e)}")
            
    def get_info(self, client_id: str) -> Dict[str, Any]:
        """Get token bucket information for client."""
        try:
            return {
                "rate": self.rate,
                "burst": self.burst,
                "remaining": self.get_remaining_tokens(client_id),
                "last_update": self.last_update.get(client_id, 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting info: {str(e)}")
            return {} 