"""Custom JSON encoder for handling datetime objects."""

import json
import traceback
from datetime import datetime
from types import TracebackType

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    
    def default(self, obj):
        """Convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, TracebackType):
            return ''.join(traceback.format_tb(obj))
        return super().default(obj) 