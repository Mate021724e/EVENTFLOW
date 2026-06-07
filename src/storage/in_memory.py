from typing import Dict, List, Optional
from src.storage.interfaces import (
    IEventRepository, IUserRepository,
    IRegistrationRepository, INotificationRepository,
)
from src.models.event import EventStatus
from src.models.user import UserStatus
from src.models.registration import RegistrationStatus


class InMemoryEventRepository(IEventRepository):
    def __init__(self):
        self._store: Dict[str, object] = {}

    def add(self, event):
        self._store[event.id] = event
        return event

    def get_by_id(self, event_id: str):
        return self._store.get(event_id)

    def get_all(self) -> List:
        return list(self._store.values())

    def update(self, event):
        self._store[event.id] = event
        return event

    def delete(self, event_id: str) -> bool:
        if event_id in self._store:
            del self._store[event_id]
            return True
        return False

    def find_by_organizer(self, organizer_id: str) -> List:
        return [e for e in self._store.values() if e.organizer_id == organizer_id]

    def find_by_category(self, category) -> List:
        return [e for e in self._store.values() if e.category == category]

    def find_available(self) -> List:
        return [e for e in self._store.values() if e.is_available()]

    def find_by_title(self, title: str) -> List:
        q = title.lower()
        return [e for e in self._store.values() if q in e.title.lower()]

    def find_by_status(self, status: EventStatus) -> List:
        return [e for e in self._store.values() if e.status == status]

    def clear(self):
        self._store.clear()

    def count(self) -> int:
        return len(self._store)


class InMemoryUserRepository(IUserRepository):
    def __init__(self):
        self._store: Dict[str, object] = {}

    def add(self, user):
        self._store[user.id] = user
        return user

    def get_by_id(self, user_id: str):
        return self._store.get(user_id)

    def get_all(self) -> List:
        return list(self._store.values())

    def update(self, user):
        self._store[user.id] = user
        return user

    def delete(self, user_id: str) -> bool:
        if user_id in self._store:
            del self._store[user_id]
            return True
        return False

    def find_by_email(self, email: str):
        for user in self._store.values():
            if user.email == email:
                return user
        return None

    def find_active(self) -> List:
        return [u for u in self._store.values() if u.status == UserStatus.ACTIVE]

    def find_blocked(self) -> List:
        return [u for u in self._store.values() if u.status == UserStatus.BLOCKED]

    def clear(self):
        self._store.clear()

    def count(self) -> int:
        return len(self._store)


class InMemoryRegistrationRepository(IRegistrationRepository):
    def __init__(self):
        self._store: Dict[str, object] = {}

    def add(self, registration):
        self._store[registration.id] = registration
        return registration

    def get_by_id(self, reg_id: str):
        return self._store.get(reg_id)

    def get_all(self) -> List:
        return list(self._store.values())

    def update(self, registration):
        self._store[registration.id] = registration
        return registration

    def find_by_user(self, user_id: str) -> List:
        return [r for r in self._store.values() if r.user_id == user_id]

    def find_by_event(self, event_id: str) -> List:
        return [r for r in self._store.values() if r.event_id == event_id]

    def find_active_by_event(self, event_id: str) -> List:
        return [r for r in self._store.values()
                if r.event_id == event_id and r.is_active()]

    def find_waitlisted(self, event_id: str) -> List:
        return [r for r in self._store.values()
                if r.event_id == event_id
                and r.status == RegistrationStatus.WAITLISTED]

    def find_by_user_and_event(self, user_id: str, event_id: str):
        for r in self._store.values():
            if r.user_id == user_id and r.event_id == event_id and r.is_active():
                return r
        return None

    def clear(self):
        self._store.clear()

    def count(self) -> int:
        return len(self._store)


class InMemoryNotificationRepository(INotificationRepository):
    def __init__(self):
        self._store: Dict[str, object] = {}

    def add(self, notification):
        self._store[notification.id] = notification
        return notification

    def get_by_id(self, notif_id: str):
        return self._store.get(notif_id)

    def get_all(self) -> List:
        return list(self._store.values())

    def find_by_user(self, user_id: str) -> List:
        return [n for n in self._store.values() if n.user_id == user_id]

    def find_unread_by_user(self, user_id: str) -> List:
        return [n for n in self._store.values()
                if n.user_id == user_id and not n.read]

    def clear(self):
        self._store.clear()

    def count(self) -> int:
        return len(self._store)
