# Python 3.13 Compatibility Notes

## Current Status

This project uses **Python 3.13.5** and has encountered compatibility issues with certain Android-specific dependencies.

## Known Issues

### pyjnius (Android Java Interface)

**Status**: ❌ **Temporarily Disabled**

**Issue**: pyjnius v1.6.1 fails to build with Python 3.13 due to the removal of the `long` built-in type.

**Error Details**:
```
jnius/jnius_utils.pxi:323:37: undeclared name not builtin: long
```

**References**:
- [Buildozer Issue #1862](https://github.com/kivy/buildozer/issues/1862)
- [Python 3.13 Changes](https://docs.python.org/3/whatsnew/3.13.html)

**Current Workaround**:
- pyjnius is disabled in `pyproject.toml` android dependencies
- All pyjnius-dependent code in `platform_utils/android.py` is commented out
- Android platform functions return fallback values

**Impact**:
- Android builds will work but without native Android API access
- Features like clipboard, notifications, and file manager will not work on Android
- Core Kivy/KivyMD functionality remains unaffected

**Resolution Timeline**:
- Monitor pyjnius releases for Python 3.13 support
- Re-enable when compatibility is restored
- Alternative: Consider downgrading to Python 3.12.x if Android API access is critical

## Working Dependencies

### Desktop Dependencies
- ✅ **plyer**: Working correctly for desktop notifications, clipboard, etc.
- ✅ **Kivy 2.3.1**: Full compatibility
- ✅ **KivyMD**: From git master, working correctly

## Migration Strategy

When pyjnius gains Python 3.13 support:

1. Uncomment imports in `platform_utils/android.py`
2. Set `ANDROID_AVAILABLE = True`
3. Uncomment implementation code
4. Re-add `"pyjnius"` to `[project.optional-dependencies].android`
5. Test Android functionality

## Alternative Solutions

If pyjnius support is delayed, consider:

1. **Python Version Downgrade**: Use Python 3.12.x
2. **Alternative Libraries**: Research pyjnius alternatives
3. **Buildozer Workarounds**: Use older Android SDK/NDK versions
4. **Direct JNI**: Implement critical Android APIs directly

## Testing Commands

```bash
# Test platform detection
uv run python -c "import platform_utils; print(f'Platform: {platform_utils.PLATFORM}')"

# Test desktop functionality
uv run --extra desktop python -c "import platform_utils; print('Desktop OK')"

# Test Android compatibility (should not fail)
uv run --extra android python -c "import platform_utils; print('Android OK')"
```

## Current Date: 2025-06-29

Last updated: M2.1 completion
Next review: When pyjnius releases Python 3.13 support 