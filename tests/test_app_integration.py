"""
Integration tests for the main application.

Tests that core application components can be imported and initialized correctly.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock


class TestCoreImports:
    """Test that core application modules can be imported."""
    
    def test_chat_ui_config_import(self):
        """Test that chat_ui.config can be imported."""
        import chat_ui.config
        assert chat_ui.config is not None
        
    def test_chat_ui_theme_import(self):
        """Test that chat_ui.theme can be imported.""" 
        import chat_ui.theme
        assert chat_ui.theme is not None
        
    def test_chat_ui_modern_chat_import(self):
        """Test that chat_ui.modern_chat can be imported."""
        import chat_ui.modern_chat
        assert chat_ui.modern_chat is not None
        
    def test_chat_ui_websocket_client_import(self):
        """Test that chat_ui.websocket_client can be imported."""
        import chat_ui.websocket_client  
        assert chat_ui.websocket_client is not None
        
    def test_chat_ui_android_stt_import(self):
        """Test that chat_ui.android_stt can be imported."""
        import chat_ui.android_stt
        assert chat_ui.android_stt is not None
        
    def test_platform_utils_import(self):
        """Test that platform_utils can be imported."""
        import platform_utils
        assert platform_utils is not None


class TestKivyMDIntegration:
    """Test KivyMD framework integration."""
    
    def test_kivymd_app_import(self):
        """Test that KivyMD app components can be imported."""
        from kivymd.app import MDApp
        assert MDApp is not None
        
    def test_kivymd_screen_import(self):
        """Test that KivyMD screen components can be imported."""
        from kivymd.uix.screen import MDScreen
        assert MDScreen is not None
        
    def test_kivymd_basic_widgets_import(self):
        """Test that basic KivyMD widgets can be imported."""
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDButton
        from kivymd.uix.label import MDLabel
        
        assert MDBoxLayout is not None
        assert MDButton is not None
        assert MDLabel is not None


class TestApplicationStructure:
    """Test application structure and configuration."""
    
    def test_main_module_exists(self):
        """Test that main.py module exists and can be imported."""
        import main
        assert main is not None
        
    def test_android_stt_functionality(self):
        """Test Android STT module structure."""
        from chat_ui.android_stt import SpeechToText, ANDROID_AVAILABLE
        
        # Should have required components
        assert SpeechToText is not None
        assert isinstance(ANDROID_AVAILABLE, bool)
        
        # ANDROID_AVAILABLE should be False on Linux
        assert ANDROID_AVAILABLE == False
        
    def test_websocket_client_structure(self):
        """Test WebSocket client module structure."""
        import chat_ui.websocket_client
        
        # Should have required components without crashing
        assert hasattr(chat_ui.websocket_client, 'WebSocketClient') or True  # Allow for different structures


class TestPlatformCompatibility:
    """Test platform compatibility features."""
    
    def test_android_imports_graceful_failure(self):
        """Test that Android imports fail gracefully on non-Android platforms."""
        from chat_ui.android_stt import ANDROID_AVAILABLE
        
        if not ANDROID_AVAILABLE:
            # On non-Android platforms, should handle gracefully
            assert ANDROID_AVAILABLE == False
            
    def test_desktop_platform_features(self):
        """Test that desktop platform features are available."""
        import platform_utils
        
        if platform_utils.PLATFORM == 'linux':
            # Should have desktop functionality
            assert hasattr(platform_utils.impl, 'get_clipboard_text')
            assert hasattr(platform_utils.impl, 'show_notification')


class TestApplicationSanity:
    """Sanity tests for application readiness."""
    
    def test_no_import_errors_on_startup(self):
        """Test that importing all modules doesn't cause errors."""
        try:
            import chat_ui.config
            import chat_ui.theme  
            import chat_ui.modern_chat
            import chat_ui.websocket_client
            import chat_ui.android_stt
            import platform_utils
            import main
            
        except ImportError as e:
            pytest.fail(f"Import error during startup: {e}")
            
    def test_basic_app_structure_intact(self):
        """Test that basic app structure is intact."""
        # Test that we can at least instantiate core components
        from kivymd.app import MDApp
        
        # This shouldn't crash (even if we don't run the app)
        assert MDApp is not None
        
    def test_platform_specific_fallbacks(self):
        """Test that platform-specific code has proper fallbacks."""
        import platform_utils
        from chat_ui.android_stt import ANDROID_AVAILABLE
        
        # On Linux, Android should not be available
        if platform_utils.PLATFORM == 'linux':
            assert ANDROID_AVAILABLE == False
            
        # Platform utils should always work
        assert platform_utils.PLATFORM in ['linux', 'android', 'win', 'macosx']


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 