"""
chat_ui/android_stt.py – fixed with safe imports
"""
try:
    from android import mActivity
    from android.runnable import run_on_ui_thread
    from android.permissions import Permission, request_permissions, check_permission
    from jnius import autoclass, PythonJavaClass, java_method
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False
    # Create a no-op decorator for desktop
    def run_on_ui_thread(func):
        """No-op decorator for non-Android platforms"""
        return func

if ANDROID_AVAILABLE:
    # Java classes
    Intent           = autoclass('android.content.Intent')
    RecognizerIntent = autoclass('android.speech.RecognizerIntent')
    SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')

    # ---------- permission ----------
    def _ensure_mic(cb):
        if check_permission(Permission.RECORD_AUDIO):
            cb()
        else:
            request_permissions([Permission.RECORD_AUDIO],
                                lambda *_: cb())

    # ---------- Python -> Java callback bridge ----------
    class CallbackWrapper(PythonJavaClass):
        __javacontext__    = 'app'
        __javainterfaces__ = ['org/kivy/speech/CallbackWrapper']

        def __init__(self, py_cb): super().__init__(); self._cb = py_cb
        @java_method('(Ljava/lang/String;Ljava/lang/String;)V')
        def callback_data(self, k, v): self._cb(str(k), str(v))

else:
    # Dummy implementations for non-Android platforms
    def _ensure_mic(cb):
        pass
    
    class CallbackWrapper:
        def __init__(self, py_cb): pass

# ---------- public helper ----------
class SpeechToText:
    def __init__(self, on_partial, on_final):
        self._on_partial, self._on_final = on_partial, on_final
        self.recognizer = None
        self.is_listening = False
        print(f"STT: Initialized with ANDROID_AVAILABLE={ANDROID_AVAILABLE}")

    # -------- lifecycle ----------
    def start(self):
        print("STT: start() called")
        if not ANDROID_AVAILABLE:
            print("STT: Android not available")
            return
        if self.is_listening:
            print("STT: Already listening, ignoring start")
            return
        print("STT: Requesting mic permission...")
        _ensure_mic(self._start_inner)

    def _start_inner(self):
        print("STT: _start_inner() called")
        if not ANDROID_AVAILABLE:
            return
        try:
            self._start_inner_android()
        except Exception as e:
            print(f"STT: Error in _start_inner: {e}")
            self.is_listening = False

    @run_on_ui_thread
    def _start_inner_android(self):
        print("STT: _start_inner_android() called")
        try:
            # Always recreate recognizer for fresh state
            if self.recognizer:
                print("STT: Cleaning up old recognizer...")
                try:
                    self.recognizer.destroy()
                except:
                    pass
                self.recognizer = None

            print("STT: Creating recognizer...")
            self._create_engine()

            if not self.recognizer:
                print("STT: ERROR - Failed to create recognizer")
                return

            print("STT: Setting up intent...")
            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            # Fix char[] warnings by using constant values directly instead of pyjnius strings
            intent.putExtra("android.speech.extra.LANGUAGE_MODEL", "free_form")
            intent.putExtra("android.speech.extra.LANGUAGE", "en-US")
            intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, True)
            intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
            
            print("STT: Starting recognition...")
            self.recognizer.startListening(intent)
            self.is_listening = True
            print("STT: Recognition started successfully")
        except Exception as e:
            print(f"STT: Error in _start_inner_android: {e}")
            self.is_listening = False
            self._cleanup_recognizer()

    def _cleanup_recognizer(self):
        """Clean up recognizer completely for fresh start"""
        print("STT: _cleanup_recognizer() called")
        try:
            if self.recognizer:
                self.recognizer.stopListening()
                self.recognizer.destroy()
                self.recognizer = None
                print("STT: Recognizer cleaned up")
        except Exception as e:
            print(f"STT: Error in cleanup: {e}")
        finally:
            self.is_listening = False

    def stop(self):
        print("STT: stop() called")
        if not ANDROID_AVAILABLE:
            return
        if not self.is_listening:
            print("STT: Not listening, ignoring stop")
            return
        self._stop_android()

    @run_on_ui_thread
    def _stop_android(self):
        print("STT: _stop_android() called")
        try:
            if self.recognizer:
                self.recognizer.stopListening()
                print("STT: Stopped listening")
                # Clean up recognizer after use to prevent state issues
                self.recognizer.destroy()
                self.recognizer = None
                print("STT: Recognizer destroyed for fresh state next time")
            self.is_listening = False
            print("STT: Stop completed")
        except Exception as e:
            print(f"STT: Error in stop: {e}")
            self.is_listening = False

    # -------- engine & listener ----------
    @run_on_ui_thread
    def _create_engine(self):
        print("STT: _create_engine() called")
        if not ANDROID_AVAILABLE:
            print("STT: Android not available in _create_engine")
            return
            
        try:
            # Use standard SpeechRecognizer (triggers system mic UI and "peep peep" sound)
            print("STT: Creating standard SpeechRecognizer...")
            self.recognizer = SpeechRecognizer.createSpeechRecognizer(mActivity)
            print("STT: Standard SpeechRecognizer created successfully")

            if not self.recognizer:
                print("STT: ERROR - Recognizer is None after creation")
                return

            print("STT: Setting up listener...")
            listener_cls = autoclass('org.kivy.speech.KivyRecognitionListener')
            listener = listener_cls(CallbackWrapper(self._dispatch))
            self.recognizer.setRecognitionListener(listener)
            print("STT: Listener set successfully")
        except Exception as e:
            print(f"STT: Error in _create_engine: {e}")
            self.recognizer = None

    # -------- router ----------
    def _dispatch(self, k, v):
        print(f"STT: _dispatch called with k='{k}', v='{v}'")
        try:
            if k == "partial":
                print(f"STT: Calling _on_partial with '{v}'")
                self._on_partial(v)
            elif k == "final":
                print(f"STT: Calling _on_final with '{v}'")
                self._on_final(v)
                # CRITICAL: Always clean up after final result to ensure fresh state next time
                print("STT: Final result received - cleaning up recognizer for fresh state")
                self._cleanup_recognizer()
            elif k == "error":
                error_code = int(v) if v.isdigit() else -1
                print(f"STT: Recognition error: {v} (code: {error_code})")
                
                # Handle specific error codes that require cleanup
                if error_code in [8, 5]:  # ERROR_RECOGNIZER_BUSY, ERROR_CLIENT
                    print(f"STT: Error {error_code} - requires cleanup")
                else:
                    print(f"STT: Error {error_code} - standard cleanup")
                
                # Always cleanup on any error
                self._cleanup_recognizer()
        except Exception as e:
            print(f"STT: Error in _dispatch: {e}")
            self._cleanup_recognizer() 