from collections import defaultdict
from typing import Callable, Dict, List, Any


class EventBus:
    """Decoupled synchronous & asynchronous event messaging bus."""
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable):
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable):
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def publish(self, event_type: str, data: Any = None):
        for handler in self._subscribers[event_type]:
            try:
                handler(data)
            except Exception as e:
                print(f"[EventBus] Handler exception on '{event_type}': {e}")


# Global default instance
event_bus = EventBus()
