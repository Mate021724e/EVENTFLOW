from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class NotificationType(Enum):
    EVENT_PUBLISHED = "event_published"
    EVENT_CANCELLED = "event_cancelled"
    EVENT_UPDATED = "event_updated"
    REGISTRATION_CONFIRMED = "registration_confirmed"
    REGISTRATION_CANCELLED = "registration_cancelled"
    WAITLIST_PROMOTED = "waitlist_promoted"
    EVENT_REMINDER = "event_reminder"
    EVENT_COMPLETED = "event_completed"


@dataclass
class Notification:
    id: str
    user_id: str
    event_id: Optional[str]
    type: NotificationType
    title: str
    message: str
    created_at: datetime = field(default_factory=datetime.now)
    read: bool = False
    read_at: Optional[datetime] = None

    def mark_read(self) -> None:
        if not self.read:
            self.read = True
            self.read_at = datetime.now()

    def __eq__(self, other):
        return isinstance(other, Notification) and self.id == other.id

    def __hash__(self):
        return hash(self.id)
