
import os
import sys

# Configure Kivy before any imports
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["KIVY_GL_BACKEND"] = "mock"
os.environ["KIVY_WINDOW"] = "mock"
os.environ["KIVY_DPI"] = "96"
os.environ["KIVY_METRICS_DENSITY"] = "1"

# Initialize metrics before KivyMD imports
from kivy.metrics import Metrics
Metrics.density = 1
Metrics.dpi = 96

# Prevent window creation during import
from kivy.base import EventLoop
def dummy_ensure_window(*args, **kwargs): pass
EventLoop.ensure_window = dummy_ensure_window
