# Android Deployment Roadmap - Micro Steps

## Phase 1: Environment Setup (Steps 1-5)

### Step 1: Install System Dependencies
```bash
# Run these commands one by one
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip
sudo apt install -y autoconf libtool pkg-config zlib1g-dev
sudo apt install -y libncurses5-dev libncursesw5-dev libtinfo5
sudo apt install -y libffi-dev libssl-dev build-essential libsqlite3-dev
```

### Step 2: Add Buildozer to Project
```bash
# Add buildozer as dev dependency
uv add --dev buildozer==1.5.0
```

### Step 3: Initialize Buildozer Config
```bash
# Generate initial buildozer.spec
uv run buildozer init
```

### Step 4: Set Environment Variables
```bash
# Add to your ~/.bashrc
echo 'export ANDROID_HOME="$HOME/.buildozer/android/platform/android-sdk"' >> ~/.bashrc
echo 'export ANDROID_NDK_HOME="$HOME/.buildozer/android/platform/android-ndk-r23c"' >> ~/.bashrc
echo 'export PATH="$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools"' >> ~/.bashrc
source ~/.bashrc
```

### Step 5: Verify Java Installation
```bash
# Check Java version (should be 17)
java -version
javac -version
```

---

## Phase 2: Dependency Updates (Steps 6-8)

### Step 6: Update pyproject.toml Dependencies
```toml
# Edit pyproject.toml - change this line:
# "kivymd>=1.2.0,<2.0.0" → "kivymd==2.0.1"
dependencies = [
    "kivymd==2.0.1",
    "kivy==2.3.1", 
    "websockets==13.1",
]
```

### Step 7: Remove Git Source for KivyMD
```toml
# Remove this section from pyproject.toml:
# [tool.uv.sources]
# kivymd = { git = "https://github.com/kivymd/KivyMD.git" }
```

### Step 8: Sync Dependencies
```bash
# Update to new versions
uv sync
```

---

## Phase 3: Basic Buildozer Config (Steps 9-12)

### Step 9: Configure App Metadata
```ini
# Edit buildozer.spec - update these lines:
[app]
title = Simple Chat
package.name = simplechat
package.domain = com.yourcompany
version = 0.1.0
```

### Step 10: Set Python Requirements
```ini
# Edit buildozer.spec - update requirements:
requirements = python3,kivy==2.3.1,kivymd==2.0.1,websockets==13.1,asyncio
```

### Step 11: Configure Android API Levels
```ini
# Edit buildozer.spec - add/update:
[android]
api = 34
minapi = 26
sdk = 34
ndk = 23c
```

### Step 12: Set ABI Targets
```ini
# Edit buildozer.spec - add:
archs = arm64-v8a,armeabi-v7a
```

---

## Phase 4: First Build Test (Steps 13-16)

### Step 13: Clean Previous Builds
```bash
# Remove any existing build artifacts
uv run buildozer android clean
```

### Step 14: First Debug Build
```bash
# Build debug APK (this will take 10-20 minutes first time)
uv run buildozer android debug
```

### Step 15: Check Build Output
```bash
# Look for APK file
ls -la bin/
# Should see: simplechat-0.1.0-arm64-v8a_armeabi-v7a-debug.apk
```

### Step 16: Install ADB Tools
```bash
# Install Android Debug Bridge
sudo apt install -y adb
```

---

## Phase 5: Device Testing (Steps 17-20)

### Step 17: Enable Developer Options on Android Device
```
# On your Android phone:
# Settings → About Phone → Tap "Build Number" 7 times
# Settings → Developer Options → Enable "USB Debugging"
```

### Step 18: Connect Device
```bash
# Connect phone via USB, then:
adb devices
# Should show your device listed
```

### Step 19: Deploy to Device
```bash
# Install and run the app
uv run buildozer android debug deploy run
```

### Step 20: Check App Launch
```bash
# Monitor logs for any startup errors
adb logcat | grep -i "python\|kivy\|simplechat" | head -20
```

---

## Phase 6: Mobile Optimizations (Steps 21-25)

### Step 21: Create Mobile Config File
```python
# Create new file: chat_ui/mobile_config.py
import platform
from kivy.metrics import dp
from kivy.utils import platform as kivy_platform

class MobileConfig:
    IS_MOBILE = kivy_platform in ('android', 'ios')
    
    if IS_MOBILE:
        BUBBLE_RADIUS = dp(12)
        HEADER_HEIGHT = dp(70)
        INPUT_HEIGHT = dp(90)
        BUTTON_SIZE = dp(56)
        MESSAGE_FONT = "14sp"
    
    HOVER_ENABLED = not IS_MOBILE
```

### Step 22: Update Theme for Mobile
```python
# Edit chat_ui/theme.py - add mobile detection:
from chat_ui.mobile_config import MobileConfig

class Sizes:
    BUBBLE_RADIUS = MobileConfig.BUBBLE_RADIUS if MobileConfig.IS_MOBILE else dp(20)
    HEADER_HEIGHT = MobileConfig.HEADER_HEIGHT if MobileConfig.IS_MOBILE else dp(60)
    INPUT_HEIGHT = MobileConfig.INPUT_HEIGHT if MobileConfig.IS_MOBILE else dp(80)
    BUTTON_SIZE = MobileConfig.BUTTON_SIZE if MobileConfig.IS_MOBILE else dp(48)
    MESSAGE_FONT = MobileConfig.MESSAGE_FONT if MobileConfig.IS_MOBILE else "16sp"
```

### Step 23: Update Main App for Mobile
```python
# Edit main.py - modify configure_kivy():
def configure_kivy():
    from kivy.utils import platform as kivy_platform
    
    if kivy_platform != 'android':
        # Only set window size on desktop
        KivyConfig.set('graphics', 'width', str(Config.WINDOW_WIDTH))
        KivyConfig.set('graphics', 'height', str(Config.WINDOW_HEIGHT))
    
    if kivy_platform == 'android':
        KivyConfig.set('kivy', 'keyboard_mode', 'system')
```

### Step 24: Add Android Back Button Handler
```python
# Edit main.py - add to ChatApp class:
def on_start(self):
    self.title = Config.APP_TITLE
    print(f"�� {Config.APP_TITLE} started successfully")
    
    # Add Android back button handling
    from kivy.utils import platform as kivy_platform
    if kivy_platform == 'android':
        from android import activity
        activity.bind(on_activity_result=self.on_activity_result)

def on_activity_result(self, request_code, result_code, intent):
    if request_code == 1:  # Back button
        return True
```

### Step 25: Test Mobile Optimizations
```bash
# Rebuild with mobile changes
uv run buildozer android debug deploy run
```

---

## Phase 7: Permissions & Security (Steps 26-30)

### Step 26: Add Required Permissions
```ini
# Edit buildozer.spec - add permissions:
[android]
permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
```

### Step 27: Create Network Security Config
```bash
# Create directory
mkdir -p assets/xml
```

### Step 28: Add Network Security File
```xml
# Create file: assets/xml/network_security_config.xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">192.168.1.223</domain>
        <domain includeSubdomains="true">localhost</domain>
    </domain-config>
</network-security-config>
```

### Step 29: Reference Security Config in Buildozer
```ini
# Edit buildozer.spec - add:
[android]
add_src = assets/xml/network_security_config.xml
```

### Step 30: Test Network Connectivity
```bash
# Rebuild and test WebSocket connection
uv run buildozer android debug deploy run
```

---

## Phase 8: Performance Tuning (Steps 31-35)

### Step 31: Add Mobile Performance Config
```python
# Edit chat_ui/config.py - add mobile overrides:
import platform
from kivy.utils import platform as kivy_platform

class Config:
    # ... existing config ...
    
    # Mobile performance overrides
    if kivy_platform == 'android':
        MAX_MESSAGE_HISTORY = 25  # Reduce from 100
        SCROLL_THROTTLE_MS = 150  # Increase from 100
        TEXT_BATCH_MS = 100       # Increase from 50
```

### Step 32: Add Memory Management
```python
# Edit chat_ui/modern_chat.py - add cleanup method:
def _cleanup_old_messages(self):
    """Remove old messages to prevent memory issues"""
    while len(self.messages.children) > self.max_messages:
        # Remove oldest message (first child)
        if self.messages.children:
            self.messages.remove_widget(self.messages.children[0])
```

### Step 33: Optimize Image Loading
```ini
# Edit buildozer.spec - add image optimization:
[android]
android.gradle_properties = android.enableJetifier=true, android.useAndroidX=true
```

### Step 34: Test Performance
```bash
# Build and test on device
uv run buildozer android debug deploy run
```

### Step 35: Monitor Memory Usage
```bash
# Check app memory usage
adb shell dumpsys meminfo com.yourcompany.simplechat
```

---

## Phase 9: Release Preparation (Steps 36-40)

### Step 36: Configure Release Build
```ini
# Edit buildozer.spec - add release config:
[android.release]
android.debuggable = False
release_artifact = aab
```

### Step 37: Add App Icon (Optional)
```bash
# Create icon directory
mkdir -p assets
# Add icon.png (512x512) to assets/
```

### Step 38: Reference Icon in Buildozer
```ini
# Edit buildozer.spec - add:
[android]
icon.filename = %(source.dir)s/assets/icon.png
```

### Step 39: Build Release AAB
```bash
# Build release version
uv run buildozer android release
```

### Step 40: Verify Release Build
```bash
# Check AAB file
ls -la bin/
# Should see: simplechat-0.1.0-arm64-v8a_armeabi-v7a-release.aab
```

---

## Phase 10: CI/CD Setup (Steps 41-45)

### Step 41: Create GitHub Actions Directory
```bash
mkdir -p .github/workflows
```

### Step 42: Create CI Workflow File
```yaml
# Create file: .github/workflows/android.yml
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
```

### Step 43: Test CI Workflow
```bash
# Commit and push to trigger CI
git add .
git commit -m "Add Android CI workflow"
git push origin main
```

### Step 44: Check CI Results
```bash
# Go to GitHub → Actions tab to monitor build
```

### Step 45: Download CI Artifact
```bash
# Download built APK from GitHub Actions artifacts
```

---

## Phase 11: Testing & Debugging (Steps 46-50)

### Step 46: Test on Multiple Devices
```bash
# Test on different Android versions if available
adb devices
# Deploy to each connected device
```

### Step 47: Test Network Scenarios
```bash
# Test with WiFi on/off
# Test with different network conditions
```

### Step 48: Test App Lifecycle
```bash
# Test app backgrounding/foregrounding
# Test memory pressure scenarios
```

### Step 49: Performance Profiling
```bash
# Monitor CPU usage
adb shell top | grep simplechat

# Monitor battery usage
adb shell dumpsys batterystats | grep simplechat
```

### Step 50: Final Validation
```bash
# Complete end-to-end test
# Verify all features work on Android
# Document any remaining issues
```

---

## Troubleshooting Quick Reference

### Common Issues & Solutions

**Build Fails:**
```bash
# Clean and retry
uv run buildozer android clean
uv run buildozer android debug
```

**App Crashes on Launch:**
```bash
# Check logs
adb logcat | grep -i "python\|kivy\|simplechat"
```

**Network Issues:**
```bash
# Verify permissions and security config
# Check WebSocket URI is accessible from device
```

**Memory Issues:**
```bash
# Reduce MAX_MESSAGE_HISTORY
# Increase throttling delays
```

Each step should take 5-15 minutes. Test thoroughly after each phase before proceeding to the next.