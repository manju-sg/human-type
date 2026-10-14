"""
Human Code Typer Package
"""

from human_typer.engine import (
    HumanTyperEngine,
    TypingProfile,
    IndentMode,
    PRESET_PROFILES,
    QWERTY_NEIGHBORS
)
from human_typer.gui import HumanTyperApp

__version__ = "1.0.0"
__all__ = [
    "HumanTyperEngine",
    "TypingProfile",
    "IndentMode",
    "PRESET_PROFILES",
    "QWERTY_NEIGHBORS",
    "HumanTyperApp"
]
