"""Custom JSON encoder for handling datetime and date objects."""

import json
import traceback
from datetime import datetime, date
from types import TracebackType

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and date objects."""
    
    def default(self, obj):
        """Convert datetime and date objects to ISO format strings."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, TracebackType):
            return ''.join(traceback.format_tb(obj))
        return super().default(obj) 