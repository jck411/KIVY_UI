# Android STT Troubleshooting Guide

This document covers common issues and solutions for Android Speech-to-Text functionality in the Kivy chat app.

## Common Issues

### 1. Microphone Button Responds But No Speech Recognition

**Symptoms:**
- Microphone button changes from 🎤 to ⏹️ when pressed
- Button state changes correctly but no actual speech recognition occurs
- No partial or final text results appear

**Possible Causes:**

#### A. Speech Recognition Service Not Available
- **Check:** Device doesn't have Google Speech Services installed
- **Solution:** Install Google app or ensure speech recognition is available on device

#### B. Permissions Issues
- **Check:** Microphone permission not properly granted
- **Solution:** Manually grant microphone permission in Android settings

#### C. Java-Python Bridge Failures
- **Check:** Callback interface not properly implemented
- **Solution:** Verify PythonCallbackWrapper is correctly bridging Java callbacks

#### D. Threading Issues
- **Check:** STT operations not running on proper threads
- **Solution:** Ensure Android STT calls are made from background threads

### 2. Debugging Steps

#### Enable Debug Logging
The STT implementation now includes comprehensive logging. To see debug output:

1. **Android Studio/ADB Logcat:**
   ```bash
   adb logcat | grep -E "(STT|🎤|🗣️|📡)"
   ```

2. **Python Logging:**
   Look for log messages with emojis like 🎤, 🗣️, 📡, ❌, ✅

#### Check STT Availability
```python
# Test if speech recognition is available
recognizer.isRecognitionAvailable(activity)
```

#### Test Permissions
```python
# Verify microphone permission
from android.permissions import check_permission, Permission
has_permission = check_permission(Permission.RECORD_AUDIO)
```

### 3. Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 1 | Network timeout | Check internet connection |
| 2 | Network error | Check network connectivity |
| 3 | Audio recording error | Check microphone hardware/permissions |
| 4 | Server error | Google Speech Services issue |
| 5 | Client error | App configuration issue |
| 6 | Speech timeout | User didn't speak within timeout |
| 7 | No speech detected | Microphone not picking up audio |
| 8 | Service busy | Recognition service overloaded |
| 9 | Insufficient permissions | Grant microphone permission |

### 4. Implementation Checklist

#### Java Classes Required:
- ✅ `CallbackWrapper.java` - Interface for callbacks
- ✅ `KivyRecognitionListener.java` - Recognition event handler

#### Python Implementation:
- ✅ `PythonCallbackWrapper` - Implements Java interface
- ✅ `AndroidSTT` - Main STT class
- ✅ Proper thread handling for Android APIs

#### Buildozer Configuration:
```ini
android.permissions = RECORD_AUDIO
android.add_src = java
requirements = ..., pyjnius
```

### 5. Testing Procedure

1. **Install fresh APK** with STT fixes
2. **Grant microphone permission** manually in Android settings
3. **Test basic functionality:**
   - Press microphone button
   - Verify button state changes
   - Check debug logs for error messages
4. **Test speech recognition:**
   - Speak clearly into microphone
   - Check for partial results
   - Verify final text appears

### 6. Common Fixes

#### If Button Responds But No Recognition:
1. Check device has Google Speech Services
2. Verify internet connection (required for cloud STT)
3. Test with different Android API levels
4. Check microphone hardware functionality

#### If Callbacks Not Received:
1. Verify Java classes are properly compiled
2. Check PythonCallbackWrapper implementation
3. Ensure proper Java method signatures
4. Test Java-Python bridge manually

#### If Permissions Issues:
1. Request permissions at runtime
2. Check Android manifest permissions
3. Test with different Android versions
4. Grant permissions manually in settings

### 7. Recovery Steps

If STT completely fails:
1. **Clean rebuild:** `buildozer android clean`
2. **Fresh install:** Uninstall and reinstall APK
3. **Reset permissions:** Clear app data in Android settings
4. **Test on different device:** Rule out device-specific issues

### 8. Known Working Configurations

- **Android API 26+** (minimum required)
- **Google Play Services** installed
- **Internet connection** available
- **Microphone permission** granted
- **pyjnius** properly installed

### 9. Debug Log Analysis

Look for this sequence in logs:
```
🎤 STT start() called
🔒 Requesting microphone permission...
🚀 Starting STT background thread...
🔧 STT _start_inner() called
🤖 Android STT initialization starting...
⚙️ Creating STT engine...
🏗️ Creating STT engine...
📱 Getting Android activity...
🗣️ Creating SpeechRecognizer...
✅ SpeechRecognizer created successfully
📄 Setting up recognition intent...
🔍 Checking if speech recognition is available...
🎙️ Starting speech recognition...
✅ STT successfully started and listening
```

If this sequence breaks, the failure point indicates the issue.

## Conclusion

Android STT is complex due to device variations, permissions, and Java-Python bridging. This guide should help identify and resolve the most common issues. When in doubt, check the debug logs first! 