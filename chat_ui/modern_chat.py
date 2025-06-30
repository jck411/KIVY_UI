"""
Modern 2025 Chat Interface - Optimized for production use
"""
import asyncio
import logging
import threading
import time 
from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFabButton
from kivymd.uix.scrollview import MDScrollView

from chat_ui.websocket_client import ChatWebSocketClient, ConnectionState
from chat_ui.theme import Colors, Sizes, Spacing, Layout
from chat_ui.config import Config, Messages

logger = logging.getLogger(__name__)

# Import STT only when on Android
try:
    from chat_ui.android_stt import SpeechToText, ANDROID_AVAILABLE
    STT_AVAILABLE = ANDROID_AVAILABLE
except ImportError:
    STT_AVAILABLE = False


class ModernBubble(MDCard):
    """Chat message bubble with optimized styling"""
    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(**kwargs)
        self.elevation = 0 if is_user else 1
        self.radius = [Sizes.BUBBLE_RADIUS]
        self.size_hint_y = None
        self.adaptive_height = True
        self.padding = [Spacing.MEDIUM, Spacing.SMALL]

        if is_user:
            self.theme_bg_color = "Custom"
            self.md_bg_color = Colors.PRIMARY_BLUE
            self.pos_hint = Layout.USER_BUBBLE_POS
            self.size_hint_x = Layout.USER_BUBBLE_WIDTH
            text_color = Colors.TEXT_LIGHT
        else:
            self.theme_bg_color = "Custom"
            self.md_bg_color = Colors.LIGHT_GRAY
            self.pos_hint = Layout.AI_BUBBLE_POS
            self.size_hint_x = Layout.AI_BUBBLE_WIDTH
            text_color = Colors.TEXT_DARK

        self.label = MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=text_color,
            font_size=Sizes.MESSAGE_FONT,
            size_hint_y=None,
            text_size=(dp(300), None),
            markup=True
        )
        self.label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        self.add_widget(self.label)

    def update_text(self, text):
        self.label.text = text


class ModernChatScreen(MDScreen):
    """
    Modern chat interface with streaming support and optimized performance.

    Features:
    - Real-time message streaming
    - Text batching for efficient updates
    - Memory management with message cleanup
    - Connection state monitoring
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = ChatWebSocketClient()
        self.current_bubble = None
        self.backend_available = False
        self.scroll_view = None
        self.connection_monitor_task = None

        # Text batching for streaming optimization
        self._pending_chunks = []
        self._text_update_scheduled = False
        self._text_batch_delay = Config.TEXT_BATCH_MS / 1000.0

        # Memory management
        self.max_messages = Config.MAX_MESSAGE_HISTORY

        self._setup_ui()
        self._initialize_connection_monitoring()

    def _initialize_connection_monitoring(self):
        Clock.schedule_once(self._test_backend, 1.0)
        self.connection_monitor_task = Clock.schedule_interval(self._monitor_connection_state, 2.0)

    def _setup_ui(self):
        layout = MDBoxLayout(
            orientation="vertical",
            theme_bg_color="Custom",
            md_bg_color=Colors.BACKGROUND
        )

        header = self._create_header()

        # Container for spacer + messages
        messages_container = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None
        )
        messages_container.bind(minimum_height=messages_container.setter('height'))

        # Flexible spacer
        spacer = Widget(size_hint_y=1)
        messages_container.add_widget(spacer)

        # Actual messages box
        self.messages = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=Spacing.MEDIUM,
            padding=[Spacing.LARGE, Spacing.LARGE]
        )
        self.messages.bind(minimum_height=self.messages.setter('height'))
        messages_container.add_widget(self.messages)

        # ScrollView
        self.scroll_view = MDScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            scroll_type=['bars', 'content'],
            bar_width=Layout.SCROLL_BAR_WIDTH,
            always_overscroll=False
        )
        self.scroll_view.add_widget(messages_container)

        # <<< THIS SINGLE LINE auto-scrolls to bottom on every new message >>>
        self.messages.bind(minimum_height=lambda inst, val: setattr(self.scroll_view, 'scroll_y', 0))

        input_card = self._create_input_area()

        # Welcome bubble
        welcome = ModernBubble(Config.WELCOME_MESSAGE)
        self.messages.add_widget(welcome)

        layout.add_widget(header)
        layout.add_widget(self.scroll_view)
        layout.add_widget(input_card)
        self.add_widget(layout)

    def _create_header(self):
        header = MDCard(
            theme_bg_color="Custom",
            md_bg_color=Colors.WHITE,
            elevation=2,
            radius=[0],
            size_hint_y=None,
            height=Sizes.HEADER_HEIGHT,
            padding=Spacing.MEDIUM
        )
        header_content = MDBoxLayout(orientation="horizontal", spacing=Spacing.SMALL)

        avatar = MDCard(
            theme_bg_color="Custom",
            md_bg_color=Colors.PRIMARY_BLUE,
            size_hint=(None, None),
            size=(Sizes.AVATAR_SIZE, Sizes.AVATAR_SIZE),
            radius=[Sizes.BUBBLE_RADIUS]
        )
        title_box = MDBoxLayout(orientation="vertical")
        title = MDLabel(
            text=Config.AI_NAME,
            font_size=Sizes.TITLE_FONT,
            bold=True,
            size_hint_y=None,
            height=dp(24)
        )
        self.status_label = MDLabel(
            text=Messages.CONNECTING,
            font_size=Sizes.STATUS_FONT,
            theme_text_color="Custom",
            text_color=Colors.TEXT_MUTED,
            size_hint_y=None,
            height=dp(18)
        )
        title_box.add_widget(title)
        title_box.add_widget(self.status_label)

        header_content.add_widget(avatar)
        header_content.add_widget(title_box)
        header.add_widget(header_content)
        return header

    def _create_input_area(self):
        input_card = MDCard(
            theme_bg_color="Custom",
            md_bg_color=Colors.WHITE,
            elevation=3,
            radius=[0],
            size_hint_y=None,
            height=Sizes.INPUT_HEIGHT,
            padding=[Spacing.LARGE, Spacing.MEDIUM]
        )
        input_box = MDBoxLayout(orientation="horizontal", spacing=Spacing.SMALL)

        self.text_input = MDTextField(
            hint_text="Type your message...",
            mode="outlined",
            font_size=Sizes.MESSAGE_FONT,
            size_hint_y=None,
            height=Sizes.BUTTON_SIZE,
            radius=[dp(24)],
            on_text_validate=self.send_message,
            # on_focus can stay if you need keyboard management, but it no longer scrolls manually
            on_focus=self._on_input_focus
        )

        if STT_AVAILABLE:
            self.mic_btn = MDFabButton(
                icon="microphone",
                theme_bg_color="Custom",
                md_bg_color=Colors.PRIMARY_BLUE,
                size_hint=(None, None),
                size=(Sizes.BUTTON_SIZE, Sizes.BUTTON_SIZE),
                on_release=self._toggle_voice
            )

        self.send_btn = MDFabButton(
            icon="send",
            theme_bg_color="Custom",
            md_bg_color=Colors.PRIMARY_BLUE,
            size_hint=(None, None),
            size=(Sizes.BUTTON_SIZE, Sizes.BUTTON_SIZE),
            on_release=self.send_message
        )

        input_box.add_widget(self.text_input)
        if STT_AVAILABLE:
            input_box.add_widget(self.mic_btn)
        input_box.add_widget(self.send_btn)
        input_card.add_widget(input_box)
        return input_card

    def send_message(self, instance):
        text = self.text_input.text.strip()
        if not text:
            return

        user_bubble = ModernBubble(text, is_user=True)
        self.messages.add_widget(user_bubble)
        self.text_input.text = ""
        self._cleanup_old_messages()
        self.current_bubble = None

        if self.backend_available:
            self._send_to_backend(text)
        else:
            self._show_demo_response(text)

    def _show_demo_response(self, message):
        demo_bubble = ModernBubble(Messages.DEMO_RESPONSE.format(message=message))
        self.messages.add_widget(demo_bubble)
        Clock.schedule_once(lambda dt: setattr(self.text_input, 'focus', True), 0.5)

    def _test_backend(self, dt):
        thread = threading.Thread(target=self._threaded_test, daemon=True)
        thread.start()

    def _threaded_test(self):
        try:
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', Messages.CONNECTING))
            future = asyncio.run_coroutine_threadsafe(
                self.client._test_connection_persistent(),
                self.client._loop
            )
            connected = future.result(timeout=Config.CONNECTION_TEST_TIMEOUT)
            self.backend_available = connected
            status_text = Messages.ONLINE if connected else Messages.DEMO_MODE
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', status_text))
        except Exception as e:
            logger.debug(f"Connection test failed: {e}")
            self.backend_available = False
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', Messages.DEMO_MODE))

    def _monitor_connection_state(self, dt):
        try:
            state = self.client.get_connection_state()
            if state == ConnectionState.CONNECTED:
                if not self.backend_available:
                    self.backend_available = True
                    self.status_label.text = Messages.ONLINE
            elif state == ConnectionState.CONNECTING:
                self.status_label.text = Messages.CONNECTING
            elif state == ConnectionState.RECONNECTING:
                self.status_label.text = Messages.RECONNECTING
            elif state in (ConnectionState.FAILED, ConnectionState.DISCONNECTED):
                self.backend_available = False
                self.status_label.text = Messages.DEMO_MODE
        except Exception:
            self.backend_available = False
            self.status_label.text = Messages.DEMO_MODE

    def _send_to_backend(self, message):
        thread = threading.Thread(target=self._threaded_send, args=(message,), daemon=True)
        thread.start()

    def _threaded_send(self, message):
        try:
            self.client.send_message_sync(message, self._on_chunk, self._on_message_complete)
        except Exception as e:
            error_msg = self._format_error_message(str(e))
            Clock.schedule_once(lambda dt: self._show_error_message(error_msg))

    def _show_error_message(self, error_msg):
        error_bubble = ModernBubble(f"❌ {error_msg}")
        self.messages.add_widget(error_bubble)
        Clock.schedule_once(lambda dt: setattr(self.text_input, 'focus', True), 0.5)

    def _format_error_message(self, error: str) -> str:
        err = error.lower()
        if "timeout" in err:
            return Messages.TIMEOUT
        if "connection refused" in err:
            return Messages.CONNECTION_REFUSED
        if "failed after" in err:
            return Messages.MAX_RETRIES
        return Messages.UNKNOWN_ERROR.format(error=error)

    def _on_chunk(self, chunk):
        self._pending_chunks.append(chunk)
        if not self._text_update_scheduled:
            self._text_update_scheduled = True
            Clock.schedule_once(self._process_batched_chunks, self._text_batch_delay)

    def _process_batched_chunks(self, dt):
        if self._pending_chunks:
            combined = ''.join(self._pending_chunks)
            self._pending_chunks.clear()
            self._append_chunk_batch(combined)
        self._text_update_scheduled = False

    def _on_message_complete(self):
        if self._pending_chunks:
            combined = ''.join(self._pending_chunks)
            self._pending_chunks.clear()
            self._append_chunk_batch(combined)
            self._text_update_scheduled = False
        Clock.schedule_once(lambda dt: setattr(self.text_input, 'focus', True), 0.1)

    def _cleanup_old_messages(self):
        if len(self.messages.children) > self.max_messages:
            to_remove = len(self.messages.children) - self.max_messages
            for _ in range(to_remove):
                self.messages.remove_widget(self.messages.children[-1])

    def _append_chunk_batch(self, text):
        if not self.current_bubble:
            self.current_bubble = ModernBubble(text)
            self.messages.add_widget(self.current_bubble)
        else:
            current_text = self.current_bubble.label.text
            self.current_bubble.update_text(current_text + text)

    def _on_input_focus(self, instance, focus):
        # no manual scrolling needed anymore
        pass

    # ========== STT Integration Methods ==========
    def _toggle_voice(self, *args):
        print("UI: _toggle_voice() called")
        current_time = time.time()
        last_press = getattr(self, '_last_mic_press', 0)
        if current_time - last_press < 0.5:
            return
        self._last_mic_press = current_time

        if not STT_AVAILABLE:
            return

        try:
            if not hasattr(self, "_stt"):
                self._stt = SpeechToText(self._on_partial, self._on_voice_done)

            is_listening = getattr(self._stt, 'is_listening', False)
            ui_voice_on = getattr(self, "_voice_on", False)

            if is_listening or ui_voice_on:
                self._stt.stop()
                self._voice_on = False
                self.mic_btn.icon = "microphone"
            else:
                self._stt.start()
                self._voice_on = True
                self.mic_btn.icon = "stop"
        except Exception as e:
            print(f"UI: STT Error in _toggle_voice: {e}")
            self._voice_on = False
            if hasattr(self, 'mic_btn'):
                self.mic_btn.icon = "microphone"
            if hasattr(self, '_stt'):
                self._stt.is_listening = False

    @mainthread
    def _on_partial(self, txt):
        if txt and txt.strip():
            self.text_input.text = txt

    @mainthread
    def _on_voice_done(self, txt):
        self._voice_on = False
        if hasattr(self, 'mic_btn'):
            self.mic_btn.icon = "microphone"
        if txt and txt.strip():
            self.text_input.text = txt
            Clock.schedule_once(lambda dt: self.send_message(None), 0.1)
