"""Android helpers via pyjnius."""

from pathlib import Path
from typing import Optional

# NOTE: pyjnius is temporarily disabled due to Python 3.13 compatibility issues
# See: https://github.com/kivy/buildozer/issues/1862
# Once pyjnius supports Python 3.13, uncomment the imports below and set ANDROID_AVAILABLE = True

try:
    # from jnius import autoclass, cast
    # from android.runnable import run_on_ui_thread
    # from android.permissions import request_permissions, Permission
    
    # # Android classes
    # PythonActivity = autoclass('org.kivy.android.PythonActivity')
    # Context = autoclass('android.content.Context')
    # Intent = autoclass('android.content.Intent')
    # Uri = autoclass('android.net.Uri')
    # Environment = autoclass('android.os.Environment')
    
    # ANDROID_AVAILABLE = True
    ANDROID_AVAILABLE = False  # Temporarily disabled
    autoclass = None
    cast = None
    run_on_ui_thread = None
    request_permissions = None
    Permission = None
except ImportError:
    # Fallback when not on Android or pyjnius not available
    ANDROID_AVAILABLE = False
    autoclass = None
    cast = None
    run_on_ui_thread = None
    request_permissions = None
    Permission = None


def get_clipboard_text() -> Optional[str]:
    """Get text from system clipboard."""
    if not ANDROID_AVAILABLE:
        return None
    
    # Implementation commented out until pyjnius Python 3.13 support
    # try:
    #     activity = PythonActivity.mActivity
    #     clipboard_manager = activity.getSystemService(Context.CLIPBOARD_SERVICE)
    #     
    #     if clipboard_manager.hasPrimaryClip():
    #         clip = clipboard_manager.getPrimaryClip()
    #         if clip.getItemCount() > 0:
    #             item = clip.getItemAt(0)
    #             return str(item.getText())
    # except Exception:
    #     pass
    
    return None


def set_clipboard_text(text: str) -> bool:
    """Set text to system clipboard."""
    if not ANDROID_AVAILABLE:
        return False
    
    # Implementation commented out until pyjnius Python 3.13 support
    # try:
    #     activity = PythonActivity.mActivity
    #     clipboard_manager = activity.getSystemService(Context.CLIPBOARD_SERVICE)
    #     
    #     ClipData = autoclass('android.content.ClipData')
    #     clip = ClipData.newPlainText("text", text)
    #     clipboard_manager.setPrimaryClip(clip)
    #     return True
    # except Exception:
    #     pass
    
    return False


def show_notification(title: str, message: str) -> bool:
    """Show system notification."""
    if not ANDROID_AVAILABLE:
        return False
    
    # Implementation commented out until pyjnius Python 3.13 support
    # try:
    #     # This would require additional setup with notification channels
    #     # For now, just return True to indicate the interface exists
    #     return True
    # except Exception:
    #     pass
    
    return False


def get_downloads_dir() -> Path:
    """Get Android downloads directory."""
    if not ANDROID_AVAILABLE:
        return Path("/sdcard/Download")
    
    # Implementation commented out until pyjnius Python 3.13 support
    # try:
    #     downloads_dir = Environment.getExternalStoragePublicDirectory(
    #         Environment.DIRECTORY_DOWNLOADS
    #     )
    #     return Path(str(downloads_dir.getAbsolutePath()))
    # except Exception:
    #     return Path("/sdcard/Download")
    
    return Path("/sdcard/Download")


def open_file_manager(path: Optional[Path] = None) -> bool:
    """Open file manager at specified path."""
    if not ANDROID_AVAILABLE:
        return False
    
    # Implementation commented out until pyjnius Python 3.13 support
    # try:
    #     activity = PythonActivity.mActivity
    #     intent = Intent(Intent.ACTION_VIEW)
    #     
    #     if path:
    #         uri = Uri.parse(f"file://{path}")
    #         intent.setDataAndType(uri, "*/*")
    #     else:
    #         intent.setType("*/*")
    #     
    #     activity.startActivity(intent)
    #     return True
    # except Exception:
    #     pass
    
    return False


def request_storage_permissions() -> bool:
    """Request storage permissions on Android."""
    if not ANDROID_AVAILABLE:
        return True  # Assume granted on non-Android
    
    # Implementation commented out until pyjnius Python 3.13 support
    # try:
    #     request_permissions([
    #         Permission.READ_EXTERNAL_STORAGE,
    #         Permission.WRITE_EXTERNAL_STORAGE
    #     ])
    #     return True
    # except Exception:
    #     return False
    
    return True


def share_text(text: str, title: str = "Share") -> bool:
    """Share text using Android's share intent."""
    if not ANDROID_AVAILABLE:
        return False
    
    # Implementation commented out until pyjnius Python 3.13 support
    # try:
    #     activity = PythonActivity.mActivity
    #     intent = Intent(Intent.ACTION_SEND)
    #     intent.setType("text/plain")
    #     intent.putExtra(Intent.EXTRA_TEXT, text)
    #     
    #     chooser = Intent.createChooser(intent, title)
    #     activity.startActivity(chooser)
    #     return True
    # except Exception:
    #     pass
    
    return False 