from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class EventStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FULL = "full"


class EventCategory(Enum):
    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    CONCERT = "concert"
    MEETUP = "meetup"
    WEBINAR = "webinar"
    SPORT = "sport"
    EXHIBITION = "exhibition"
    OTHER = "other"


@dataclass
class Event:
    id: str
    title: str
    description: str
    organizer_id: str
    category: EventCategory
    start_dt: datetime
    end_dt: datetime
    location: str
    capacity: int
    price: float = 0.0
    status: EventStatus = EventStatus.DRAFT
    registered_count: int = 0
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def is_available(self) -> bool:
        return (
            self.status == EventStatus.PUBLISHED
            and self.registered_count < self.capacity
        )

    def is_free(self) -> bool:
        return self.price == 0.0

    def spots_left(self) -> int:
        return max(0, self.capacity - self.registered_count)

    def register_spot(self) -> bool:
        if self.is_available():
            self.registered_count += 1
            if self.registered_count >= self.capacity:
                self.status = EventStatus.FULL
            return True
        return False

    def unregister_spot(self) -> None:
        if self.registered_count > 0:
            self.registered_count -= 1
            if self.status == EventStatus.FULL:
                self.status = EventStatus.PUBLISHED

    def publish(self) -> bool:
        if self.status == EventStatus.DRAFT:
            self.status = EventStatus.PUBLISHED
            return True
        return False

    def cancel(self) -> bool:
        if self.status in (EventStatus.DRAFT, EventStatus.PUBLISHED, EventStatus.FULL):
            self.status = EventStatus.CANCELLED
            return True
        return False

    def complete(self) -> bool:
        if self.status in (EventStatus.PUBLISHED, EventStatus.FULL):
            self.status = EventStatus.COMPLETED
            return True
        return False

    def duration_hours(self) -> float:
        delta = self.end_dt - self.start_dt
        return delta.total_seconds() / 3600

    def __eq__(self, other):
        return isinstance(other, Event) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"Event(id={self.id!r}, title={self.title!r}, status={self.status})"
