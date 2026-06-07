from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class PlatformEvent(Enum):
    EVENT_PUBLISHED = "event_published"
    EVENT_CANCELLED = "event_cancelled"
    EVENT_UPDATED = "event_updated"
    EVENT_COMPLETED = "event_completed"
    REGISTRATION_CONFIRMED = "registration_confirmed"
    REGISTRATION_CANCELLED = "registration_cancelled"
    WAITLIST_PROMOTED = "waitlist_promoted"
    EVENT_FULL = "event_full"
    SPOT_FREED = "spot_freed"


class IPlatformObserver(ABC):
    @abstractmethod
    def on_event(self, event: PlatformEvent, data: Dict[str, Any]) -> None: ...


class PlatformEventBus:
    def __init__(self):
        self._observers: Dict[PlatformEvent, List[IPlatformObserver]] = {}
        self._event_log: List[Dict] = []

    def subscribe(self, event: PlatformEvent, observer: IPlatformObserver) -> None:
        if event not in self._observers:
            self._observers[event] = []
        if observer not in self._observers[event]:
            self._observers[event].append(observer)

    def unsubscribe(self, event: PlatformEvent, observer: IPlatformObserver) -> None:
        if event in self._observers:
            self._observers[event] = [o for o in self._observers[event] if o is not observer]

    def publish(self, event: PlatformEvent, data: Dict[str, Any] = None) -> None:
        payload = data or {}
        self._event_log.append({'event': event, 'data': payload})
        for observer in self._observers.get(event, []):
            observer.on_event(event, payload)

    def get_event_log(self) -> List[Dict]:
        return list(self._event_log)

    def clear_log(self) -> None:
        self._event_log.clear()


class NotificationObserver(IPlatformObserver):
    def __init__(self):
        self.received: List[Dict] = []

    def on_event(self, event: PlatformEvent, data: Dict[str, Any]) -> None:
        self.received.append({'event': event, 'data': data})

    def get_received(self) -> List[Dict]:
        return list(self.received)

    def clear(self) -> None:
        self.received.clear()


class AuditObserver(IPlatformObserver):
    def __init__(self):
        self.log: List[str] = []

    def on_event(self, event: PlatformEvent, data: Dict[str, Any]) -> None:
        self.log.append(f"[{datetime.now().isoformat()}] {event.value}: {data}")

    def get_log(self) -> List[str]:
        return list(self.log)


class WaitlistObserver(IPlatformObserver):
    def __init__(self):
        self.promotions: List[Dict] = []

    def on_event(self, event: PlatformEvent, data: Dict[str, Any]) -> None:
        if event == PlatformEvent.WAITLIST_PROMOTED:
            self.promotions.append(data)

    def get_promotions(self) -> List[Dict]:
        return list(self.promotions)

    def clear(self) -> None:
        self.promotions.clear()
