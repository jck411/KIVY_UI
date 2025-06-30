"""
Theme constants for consistent styling across the chat UI
Optimized for production use with type hints and better organization
"""
from typing import List, Union
from kivy.metrics import dp, sp, Metrics
from kivy.utils import get_color_from_hex

# Ensure metrics system is initialized with fallback values
if not hasattr(Metrics, 'density') or Metrics.density is None:
    Metrics.density = 1
if not hasattr(Metrics, 'dpi') or Metrics.dpi is None:
    Metrics.dpi = 96

def safe_dp(value: Union[int, float]) -> float:
    """Safely convert value to dp with fallback"""
    try:
        return dp(value)
    except (TypeError, ValueError):
        return float(value)

def safe_sp(value: Union[int, float]) -> float:
    """Safely convert value to sp with fallback"""
    try:
        return sp(value)
    except (TypeError, ValueError):
        return float(value)

class Colors:
    """Color palette for the chat interface with KivyMD 2.0+ compatibility"""
    # RGBA lists (0-1 range) for KivyMD 2.0+ compatibility
    PRIMARY_BLUE: List[float] = [0.13, 0.59, 0.95, 1]  # #2196F3
    WHITE: List[float] = [1, 1, 1, 1]  # #FFFFFF
    LIGHT_GRAY: List[float] = [0.96, 0.96, 0.96, 1]  # #F5F5F5
    BACKGROUND: List[float] = [0.98, 0.98, 0.98, 1]  # #FAFAFA
    TEXT_DARK: List[float] = [0.1, 0.1, 0.1, 1]  # #1A1A1A
    TEXT_LIGHT: List[float] = [1, 1, 1, 1]  # #FFFFFF
    TEXT_MUTED: List[float] = [0.5, 0.5, 0.5, 1]  # #808080
    
    # Hex colors for alternative use (though lists are preferred in KivyMD 2.0+)
    PRIMARY_BLUE_HEX: str = "#2196F3"
    WHITE_HEX: str = "#FFFFFF"
    LIGHT_GRAY_HEX: str = "#F5F5F5"
    BACKGROUND_HEX: str = "#FAFAFA"
    TEXT_DARK_HEX: str = "#1A1A1A"
    TEXT_LIGHT_HEX: str = "#FFFFFF"
    TEXT_MUTED_HEX: str = "#808080"
    
    @staticmethod
    def hex_to_list(hex_color: str) -> List[float]:
        """Convert hex color to RGBA list format for KivyMD 2.0+"""
        return list(get_color_from_hex(hex_color))


class Sizes:
    """Size constants for UI elements in device-independent pixels"""
    BUBBLE_RADIUS = safe_dp(20)
    HEADER_HEIGHT = safe_dp(60)
    INPUT_HEIGHT = safe_dp(80)
    BUTTON_SIZE = safe_dp(48)
    AVATAR_SIZE = safe_dp(40)
    
    # Text sizes (using sp for scalable pixels)
    TITLE_FONT = "18sp"
    STATUS_FONT = "14sp"
    MESSAGE_FONT = "16sp"


class Spacing:
    """Spacing constants for consistent layout margins and padding"""
    SMALL = safe_dp(12)
    MEDIUM = safe_dp(16)
    LARGE = safe_dp(20)


class Layout:
    """Layout-specific constants and ratios"""
    USER_BUBBLE_WIDTH: float = 0.8
    AI_BUBBLE_WIDTH: float = 0.85
    USER_BUBBLE_POS = {"right": 0.95}
    AI_BUBBLE_POS = {"x": 0.05}
    SCROLL_BAR_WIDTH = safe_dp(4) 