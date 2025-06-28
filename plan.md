

# Android Deployment Roadmap for KivyMD Chat UI

## 1. Stack Audit & Version Mapping

### Current Desktop Stack → Android-Safe Versions (2025)

**Core Framework**
- **Python**: 3.11 → **3.12.7** (latest p4a support)
- **Kivy**: 2.3.1 → **2.3.1** ✅ (Android-compatible)
- **KivyMD**: dev branch → **2.0.1** (stable release required)
- **WebSockets**: 13.1 → **13.1** ✅ (pure Python, Android-compatible)

**Dependencies Audit**
```bash
# Current pyproject.toml audit
websockets>=13.1          # ✅ Pure Python, Android-safe
kivymd>=1.2.0,<2.0.0     # ❌ Change to stable 2.0.1
kivy>=2.3.1              # ✅ Android-compatible
```

**No C-extensions detected** → No custom p4a recipes needed

**Version Lock Strategy**
```toml
# pyproject.toml Android updates
[project]
dependencies = [
    "kivymd==2.0.1",           # Stable release
    "kivy==2.3.1",             # Pin exact version
    "websockets==13.1",        # Pin for consistency
]
```

---

## 2. Android Build Toolchain Setup

### Install Buildozer + Dependencies (Ubuntu)

```bash
# 1. System dependencies
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config
sudo apt install -y zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5
sudo apt install -y libffi-dev libssl-dev build-essential libsqlite3-dev

# 2. Install buildozer via uv (preferred)
uv add --dev buildozer==1.5.0

# 3. Android SDK/NDK versions (2025-compatible)
export ANDROID_HOME="$HOME/.buildozer/android/platform/android-sdk"
export ANDROID_NDK_HOME="$HOME/.buildozer/android/platform/android-ndk-r23c"
export PATH="$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools"
```

**Required Versions**
- **JDK**: OpenJDK 17 (Android Gradle Plugin 8.x requirement)
- **Android SDK**: API 34 (Android 14, current target)
- **NDK**: r23c (latest p4a support)
- **Gradle**: 8.4 (managed by buildozer)
- **Build Tools**: 34.0.0

---

## 3. Minimal buildozer.spec Configuration

### Complete buildozer.spec Template

```ini
# buildozer.spec - Android build configuration
[app]
title = Simple Chat
package.name = simplechat
package.domain = com.yourcompany

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_dirs = tests,bin,venv,.git,__pycache__,.pytest_cache

version = 0.1.0
requirements = python3,kivy==2.3.1,kivymd==2.0.1,websockets==13.1,asyncio

[buildozer]
log_level = 2
warn_on_root = 1

# Android-specific
[android]
# API levels (2025 targets)
api = 34                    # Target latest Android 14
minapi = 26                 # Support Android 8.0+ (2018+)
sdk = 34                    # Build tools version
ndk = 23c                   # NDK version for compatibility

# ABI targets - arm64 primary, armeabi-v7a fallback
archs = arm64-v8a,armeabi-v7a

# Package format - AAB for Play Store
release_artifact = aab

# Permissions - minimal set
permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK

# App metadata
android.manifest_placeholders = [app_name:Simple Chat]
android.allow_backup = True
android.theme = @android:style/Theme.NoTitleBar

# Orientation - allow both portrait/landscape
orientation = portrait

# Icon/splash (optional)
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/splash.png

# Build optimization
android.gradle_dependencies = 
android.add_src = 
android.add_aars = 
android.add_jars = 

# Debug/release configs
[android.debug]
android.debuggable = True

[android.release]
android.debuggable = False
# For production: add signing config
# android.keystore = ~/.keystore/release.keystore
# android.keyalias = mykey
```

**Key Option Explanations**
- **API 34/minAPI 26**: Targets 95%+ devices (Android 8.0+)
- **arm64-v8a**: Primary ABI for modern phones (2019+)
- **armeabi-v7a**: Fallback for older devices
- **AAB format**: Required for Play Store, smaller downloads
- **Minimal permissions**: Only network access needed

---

## 4. Replace Desktop-Only Utilities

### Audit Complete ✅
**No desktop dependencies found**
- No `xclip`/`xsel` usage detected
- No platform-specific clipboard code
- Pure Kivy/KivyMD implementation

### Recommended Cross-Platform Additions
```python
# Optional: Add Plyer for enhanced mobile features
# requirements = ...,plyer==2.1.0

# Example mobile clipboard (if needed later)
try:
    from plyer import clipboard
    clipboard.copy("text")
    text = clipboard.paste()
except ImportError:
    # Fallback to Kivy clipboard
    from kivy.core.clipboard import Clipboard
    Clipboard.copy("text")
```

---

## 5. Mobile Ergonomics Tweaks

### Essential Mobile Adaptations

```python
# chat_ui/mobile_config.py - New file
import platform
from kivy.metrics import dp
from kivy.utils import platform as kivy_platform

class MobileConfig:
    """Mobile-specific configuration overrides"""
    
    IS_MOBILE = kivy_platform in ('android', 'ios')
    
    # DPI scaling for mobile screens
    if IS_MOBILE:
        BUBBLE_RADIUS = dp(12)      # Smaller radius on mobile
        HEADER_HEIGHT = dp(70)      # Taller for touch targets  
        INPUT_HEIGHT = dp(90)       # Bigger input area
        BUTTON_SIZE = dp(56)        # Material Design touch target
        MESSAGE_FONT = "14sp"       # Smaller font for mobile
    
    # Touch vs hover behavior
    HOVER_ENABLED = not IS_MOBILE
    
    # Storage paths
    if IS_MOBILE and kivy_platform == 'android':
        from android.storage import primary_external_storage_path
        STORAGE_PATH = primary_external_storage_path()
    else:
        STORAGE_PATH = "."

# main.py updates
def configure_kivy():
    """Mobile-aware Kivy configuration"""
    if MobileConfig.IS_MOBILE:
        # Remove desktop-specific window settings
        pass
    else:
        KivyConfig.set('graphics', 'width', str(Config.WINDOW_WIDTH))
        KivyConfig.set('graphics', 'height', str(Config.WINDOW_HEIGHT))
    
    # Mobile keyboard behavior
    if kivy_platform == 'android':
        KivyConfig.set('kivy', 'keyboard_mode', 'system')

# Handle Android back button
class ChatApp(MDApp):
    def on_start(self):
        if kivy_platform == 'android':
            from android import activity
            activity.bind(on_activity_result=self.on_activity_result)
    
    def on_activity_result(self, request_code, result_code, intent):
        """Handle back button on Android"""
        if request_code == 1:  # Back button
            return True  # Consume event
```

### Network I/O Threading Rules
```python
# Already compliant - your websocket_client.py correctly uses:
# ✅ Background threading for network operations
# ✅ Clock.schedule_once() for UI updates
# ✅ Asyncio in separate thread (Android-safe)
```

---

## 6. Build–Deploy–Debug Loop

### Complete Command Sequence

```bash
# 1. Initial setup (run once)
uv run buildozer init
uv run buildozer android clean

# 2. Debug build and test
uv run buildozer android debug

# 3. Deploy to connected device
uv run buildozer android debug deploy run

# 4. Monitor logs in real-time
adb logcat | grep -i "python\|kivy\|simplechat"

# 5. Optimized log filtering
adb logcat -s "python:*" "PythonService:*" "SDL:*" | grep -v "DEBUG"

# 6. Debug-specific commands
uv run buildozer android debug deploy run logcat

# 7. Release build (production)
uv run buildozer android release
```

### Logcat Interpretation Tips

**Common Error Patterns**
```bash
# Missing recipe error
"Recipe for xyz not found" → Add to requirements or find alternative

# ABI mismatch  
"INSTALL_PARSE_FAILED_NO_CERTIFICATES" → Clean build directory

# Permission denied
"Permission denied" → Check android.permissions in buildozer.spec

# Python import errors
"ImportError" → Verify all dependencies in requirements
```

**Debugging Commands**
```bash
# Device info
adb devices
adb shell getprop ro.product.cpu.abi

# App-specific logs
adb logcat | grep "$(adb shell ps | grep simplechat | awk '{print $2}')"

# Clear app data for fresh test
adb shell pm clear com.yourcompany.simplechat
```

---

## 7. CI Automation

### GitHub Actions Android Build

```yaml
# .github/workflows/android.yml
name: Android Build

on:
  push:
    branches: [ main, android ]
  pull_request:
    branches: [ main ]

jobs:
  build-android:
    runs-on: ubuntu-22.04
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python 3.12
      uses: actions/setup-python@v4
      with:
        python-version: '3.12.7'
    
    - name: Install uv
      uses: astral-sh/setup-uv@v1
      with:
        version: "latest"
    
    - name: Install system dependencies
      run: |
        sudo apt update
        sudo apt install -y openjdk-17-jdk autoconf libtool pkg-config
        sudo apt install -y zlib1g-dev libncurses5-dev libffi-dev libssl-dev
    
    - name: Cache buildozer directory
      uses: actions/cache@v3
      with:
        path: ~/.buildozer
        key: buildozer-${{ runner.os }}-${{ hashFiles('buildozer.spec') }}
        restore-keys: |
          buildozer-${{ runner.os }}-
    
    - name: Install dependencies
      run: |
        uv sync
        uv add --dev buildozer==1.5.0
    
    - name: Build Android Debug APK
      run: |
        uv run buildozer android debug
        
    - name: Upload APK artifact
      uses: actions/upload-artifact@v3
      with:
        name: android-debug-apk
        path: bin/*.apk
        retention-days: 30

    # Optional: Auto-release on tags
    - name: Create Release
      if: startsWith(github.ref, 'refs/tags/')
      uses: softprops/action-gh-release@v1
      with:
        files: bin/*.apk
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**CI Optimizations**
- **Caching**: `~/.buildozer` cache saves 10-15 minutes per build
- **Artifact retention**: 30 days for debug builds
- **Auto-release**: Tagged commits create GitHub releases

---

## 8. Common Gotchas & Fixes

### OpenSSL/TLS Issues
```bash
# Symptom: SSL certificate errors
# Fix: Add SSL context configuration
# In websocket_client.py:
import ssl
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  # Only for development
```

### Java/Gradle Errors
```bash
# Error: "Could not find method compile()"
# Fix: Update buildozer.spec
[android]
gradle_dependencies = 

# Error: "Unsupported Java version"  
# Fix: Ensure OpenJDK 17
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### Large APK Size (>100MB)
```bash
# Reduce APK size strategies:
# 1. Single ABI builds
archs = arm64-v8a  # Remove armeabi-v7a for primary release

# 2. Exclude unnecessary files
source.exclude_dirs = tests,bin,venv,.git,__pycache__,.pytest_cache,docs

# 3. Enable APK splitting
android.allow_backup = False
android.gradle_properties = android.enableJetifier=true, android.useAndroidX=true
```

### Android 13+ Runtime Permissions
```python
# Add runtime permission requests for Android 13+
# In main.py
def request_permissions():
    """Request runtime permissions on Android 13+"""
    if kivy_platform == 'android':
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.INTERNET,
            Permission.ACCESS_NETWORK_STATE,
        ])

# Call in ChatApp.on_start()
```

### Memory Issues on Low-End Devices
```python
# In chat_ui/config.py - mobile overrides
if kivy_platform == 'android':
    MAX_MESSAGE_HISTORY = 25  # Reduce from 100
    SCROLL_THROTTLE_MS = 150  # Increase from 100
    TEXT_BATCH_MS = 100       # Increase from 50
```

### WebSocket Connection Issues
```python
# Android network security - add network_security_config.xml
# buildozer.spec addition:
android.add_src = assets/xml/network_security_config.xml

# assets/xml/network_security_config.xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">192.168.1.223</domain>
        <domain includeSubdomains="true">localhost</domain>
    </domain-config>
</network-security-config>
```

**Build Process Troubleshooting**
1. **Clean builds**: `buildozer android clean` before major changes
2. **Dependency conflicts**: Pin all versions in requirements
3. **Storage space**: Buildozer needs 5-10GB free space
4. **Network timeouts**: Use `--verbose` flag for detailed logs
5. **ABI mismatches**: Test on real devices, not just emulators

This roadmap provides a complete path from your working desktop app to production Android deployment, with specific version targets and common issue prevention.