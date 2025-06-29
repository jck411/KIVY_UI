"""Desktop helpers (clipboard, notifications, file dialogs)."""

import os
import subprocess
from pathlib import Path
from typing import Optional


def get_clipboard_text() -> Optional[str]:
    """Get text from system clipboard."""
    try:
        # Try xclip first
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Try xsel as fallback
        result = subprocess.run(
            ["xsel", "--clipboard", "--output"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None


def set_clipboard_text(text: str) -> bool:
    """Set text to system clipboard."""
    try:
        # Try xclip first
        result = subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Try xsel as fallback
        result = subprocess.run(
            ["xsel", "--clipboard", "--input"],
            input=text,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return False


def show_notification(title: str, message: str) -> bool:
    """Show system notification."""
    try:
        subprocess.run(
            ["notify-send", title, message],
            timeout=5,
            check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def get_downloads_dir() -> Path:
    """Get user's downloads directory."""
    home = Path.home()
    downloads = home / "Downloads"
    if downloads.exists():
        return downloads
    return home


def open_file_manager(path: Optional[Path] = None) -> bool:
    """Open file manager at specified path."""
    if path is None:
        path = Path.home()
    
    try:
        subprocess.run(
            ["xdg-open", str(path)],
            timeout=5,
            check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False 