from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class UserRole(Enum):
    PARTICIPANT = "participant"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class UserStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"


@dataclass
class User:
    id: str
    name: str
    email: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    registrations: List[str] = field(default_factory=list)
    organized_events: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    blocked_at: Optional[datetime] = None
    block_reason: Optional[str] = None

    MAX_REGISTRATIONS = 10

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def is_blocked(self) -> bool:
        return self.status == UserStatus.BLOCKED

    def can_register(self) -> bool:
        return self.is_active() and len(self.registrations) < self.MAX_REGISTRATIONS

    def can_organize(self) -> bool:
        return self.is_active() and self.role in (UserRole.ORGANIZER, UserRole.ADMIN)

    def block(self, reason: str) -> None:
        self.status = UserStatus.BLOCKED
        self.blocked_at = datetime.now()
        self.block_reason = reason

    def unblock(self) -> None:
        self.status = UserStatus.ACTIVE
        self.blocked_at = None
        self.block_reason = None

    def add_registration(self, registration_id: str) -> None:
        if registration_id not in self.registrations:
            self.registrations.append(registration_id)

    def remove_registration(self, registration_id: str) -> None:
        if registration_id in self.registrations:
            self.registrations.remove(registration_id)

    def add_organized_event(self, event_id: str) -> None:
        if event_id not in self.organized_events:
            self.organized_events.append(event_id)

    def __eq__(self, other):
        return isinstance(other, User) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.name!r}, role={self.role})"
