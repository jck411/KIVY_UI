"""Type stubs for android.runnable module"""

from typing import Any, Protocol

class Runnable(Protocol):
    def run(self) -> None: ... 