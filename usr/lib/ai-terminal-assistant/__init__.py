"""
AI Terminal Assistant Library
Author: surajraktate
"""

__version__ = "1.0.0"
__author__ = "Suraj Raktate"
__email__ = "raktatesuraj@gmail.com"

from .ai_assistant import AITerminalAssistant
from .config import ConfigManager
from .security import CommandValidator, SecurityError

__all__ = [
    'AITerminalAssistant',
    'ConfigManager',
    'CommandValidator',
    'SecurityError'
]