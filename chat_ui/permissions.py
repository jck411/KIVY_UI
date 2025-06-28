"""
Runtime permissions helper for Android STT
"""
from android.permissions import request_permissions, Permission, check_permission

def ensure_audio_permission(cb_done=None):
    """
    Ask for RECORD_AUDIO at runtime if we don't have it yet.
    cb_done – optional callback (perms, results) -> None.
    """
    if check_permission(Permission.RECORD_AUDIO):
        if cb_done: 
            cb_done([Permission.RECORD_AUDIO], [True])
        return True
    
    request_permissions([Permission.RECORD_AUDIO], cb_done)
    return False 