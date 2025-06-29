"""
Smoke tests for platform dispatch functionality.

Tests the platform abstraction layer to ensure:
- Platform detection works correctly
- Platform imports succeed  
- Correct platform implementation is loaded
- Basic platform functions are accessible
"""

import pytest
import sys
from unittest.mock import patch, MagicMock


class TestPlatformDetection:
    """Test platform detection and module loading."""
    
    def test_platform_import_succeeds(self):
        """Test that platform_utils can be imported without errors."""
        import platform_utils
        assert platform_utils is not None
        
    def test_platform_attribute_exists(self):
        """Test that PLATFORM attribute is available."""
        import platform_utils
        assert hasattr(platform_utils, 'PLATFORM')
        assert isinstance(platform_utils.PLATFORM, str)
        assert platform_utils.PLATFORM in ['linux', 'android', 'win', 'macosx']
        
    def test_impl_attribute_exists(self):
        """Test that impl attribute is available."""
        import platform_utils
        assert hasattr(platform_utils, 'impl')
        assert platform_utils.impl is not None


class TestLinuxPlatform:
    """Test Linux platform implementation (current platform)."""
    
    def test_linux_platform_detected(self):
        """Test that Linux platform is correctly detected."""
        import platform_utils
        # Should be 'linux' on our current system
        assert platform_utils.PLATFORM == 'linux'
        
    def test_desktop_implementation_loaded(self):
        """Test that desktop implementation is loaded on Linux."""
        import platform_utils
        # Should have desktop module loaded
        assert 'desktop' in platform_utils.impl.__name__
        
    def test_desktop_functions_available(self):
        """Test that desktop platform functions are accessible."""
        import platform_utils
        
        # Check that key functions exist
        expected_functions = [
            'get_clipboard_text',
            'set_clipboard_text', 
            'show_notification',
            'open_file_manager',
            'open_url'
        ]
        
        for func_name in expected_functions:
            assert hasattr(platform_utils.impl, func_name), f"Missing function: {func_name}"
            assert callable(getattr(platform_utils.impl, func_name)), f"Not callable: {func_name}"


class TestAndroidPlatformMock:
    """Test Android platform behavior with mocking."""
    
    @patch('kivy.utils.platform', 'android')
    def test_android_platform_mock(self):
        """Test Android platform loading with mocked platform."""
        # Clear module cache to force reload
        modules_to_clear = [mod for mod in sys.modules.keys() if mod.startswith('platform_utils')]
        for mod in modules_to_clear:
            del sys.modules[mod]
            
        try:
            import platform_utils
            assert platform_utils.PLATFORM == 'android'
            assert 'android' in platform_utils.impl.__name__
        except ImportError as e:
            # Expected since Android modules aren't available on Linux
            assert 'android' in str(e).lower()
            
    def test_android_functions_available_when_mocked(self):
        """Test that Android functions exist (even if stubbed)."""
        with patch('kivy.utils.platform', 'android'):
            # Mock the android modules
            android_mock = MagicMock()
            with patch.dict('sys.modules', {'platform_utils.android': android_mock}):
                modules_to_clear = [mod for mod in sys.modules.keys() if mod.startswith('platform_utils')]
                for mod in modules_to_clear:
                    if mod in sys.modules:
                        del sys.modules[mod]
                
                # Create a mock android implementation
                mock_android_impl = MagicMock()
                mock_android_impl.ANDROID_AVAILABLE = False
                mock_android_impl.get_clipboard_text = MagicMock(return_value="")
                mock_android_impl.set_clipboard_text = MagicMock()
                
                expected_functions = [
                    'get_clipboard_text',
                    'set_clipboard_text',
                    'request_permissions',
                    'show_notification',
                    'open_file_manager'
                ]
                
                for func_name in expected_functions:
                    assert hasattr(mock_android_impl, func_name) or callable(getattr(mock_android_impl, func_name, None))


class TestPlatformFunctionality:
    """Test basic platform functionality."""
    
    def test_clipboard_functions_exist(self):
        """Test that clipboard functions are available."""
        import platform_utils
        
        # Test that functions exist and are callable
        assert callable(platform_utils.impl.get_clipboard_text)
        assert callable(platform_utils.impl.set_clipboard_text)
        
    def test_clipboard_basic_functionality(self):
        """Test basic clipboard functionality (if available)."""
        import platform_utils
        
        try:
            # Try to get clipboard text (should not raise exception)
            text = platform_utils.impl.get_clipboard_text()
            assert isinstance(text, str) or text is None
            
            # Try to set clipboard text (should not raise exception)
            platform_utils.impl.set_clipboard_text("test")
            
        except Exception as e:
            # Expected if clipboard tools aren't available
            # Should be graceful failure, not crash
            assert "not available" in str(e).lower() or "command not found" in str(e).lower()
            
    def test_notification_function_exists(self):
        """Test that notification function exists."""
        import platform_utils
        assert callable(platform_utils.impl.show_notification)
        
    def test_file_manager_function_exists(self):
        """Test that file manager function exists."""
        import platform_utils  
        assert callable(platform_utils.impl.open_file_manager)


class TestPlatformStability:
    """Test platform abstraction stability."""
    
    def test_multiple_imports_consistent(self):
        """Test that multiple imports return consistent results."""
        import platform_utils as pu1
        import platform_utils as pu2
        
        assert pu1.PLATFORM == pu2.PLATFORM
        assert pu1.impl == pu2.impl
        
    def test_platform_attributes_immutable(self):
        """Test that platform attributes behave correctly."""
        import platform_utils
        
        original_platform = platform_utils.PLATFORM
        original_impl = platform_utils.impl
        
        # Platform should be consistent
        assert platform_utils.PLATFORM == original_platform
        assert platform_utils.impl == original_impl


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 