"""
Configuration module for kagent.
"""

import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_model_client_config() -> Dict[str, Any]:
    """
    Get the model client configuration.
    
    Returns:
        Dict[str, Any]: The model client configuration.
    """
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_API_BASE"),
        "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
    }

def get_default_model_client():
    """
    Get the default model client.
    
    Returns:
        Any: The default model client.
    """
    logger.warning("Model client functionality is not available in this version")
    return None 