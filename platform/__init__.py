"""Platform abstraction layer for cross-platform compatibility."""

from kivy.utils import platform as _platform

if _platform == "linux":
    from . import desktop as impl
elif _platform == "android":
    from . import android as impl
else:
    raise ImportError(f"Unsupported platform: {_platform}")

__all__ = ["impl"] 