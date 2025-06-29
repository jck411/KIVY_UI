"""Platform abstraction layer for cross-platform compatibility."""

from kivy.utils import platform as _platform

# Expose the detected platform
PLATFORM = _platform

if _platform == "linux":
    from . import desktop as impl
elif _platform == "android":
    from . import android as impl
else:
    raise ImportError(f"Unsupported platform: {_platform}")

# Expose common interface
__all__ = ["PLATFORM", "impl"] 