"""Selection synchronization and cross-probing bridge."""

from __future__ import annotations

from typing import Callable, Dict, List


class SelectionBridge:
    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[[str], None]]] = {}

    def subscribe(self, channel: str, callback: Callable[[str], None]) -> None:
        listeners = self._listeners.setdefault(channel, [])
        if callback not in listeners:
            listeners.append(callback)

    def unsubscribe(self, channel: str, callback: Callable[[str], None]) -> None:
        listeners = self._listeners.get(channel, [])
        if callback in listeners:
            listeners.remove(callback)

    def clear(self) -> None:
        self._listeners.clear()

    def publish(self, channel: str, stable_id: str) -> None:
        for callback in self._listeners.get(channel, []):
            callback(stable_id)
