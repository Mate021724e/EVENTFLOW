from datetime import datetime
from typing import List, Optional
from src.models.event import Event, EventStatus, EventCategory
from src.storage.interfaces import IEventRepository, IEventSortStrategy
from src.services.observer import PlatformEventBus, PlatformEvent
from src.services.sort_strategies import SortByDateAscStrategy
from src.utils.id_generator import generate_event_id
from src.utils.exceptions import (
    EventNotFoundError, InsufficientPermissionsError,
    InvalidEventDatesError, EventNotEditableError,
)


class EventService:
    def __init__(
        self,
        event_repo: IEventRepository,
        sort_strategy: Optional[IEventSortStrategy] = None,
        event_bus: Optional[PlatformEventBus] = None,
    ):
        self._repo = event_repo
        self._sort = sort_strategy or SortByDateAscStrategy()
        self._bus = event_bus or PlatformEventBus()

    def create_event(
        self,
        title: str,
        description: str,
        organizer_id: str,
        category: EventCategory,
        start_dt: datetime,
        end_dt: datetime,
        location: str,
        capacity: int,
        price: float = 0.0,
        tags: Optional[List[str]] = None,
    ) -> Event:
        if end_dt <= start_dt:
            raise InvalidEventDatesError("end must be after start")
        if capacity <= 0:
            raise InvalidEventDatesError("capacity must be positive")
        event = Event(
            id=generate_event_id(),
            title=title,
            description=description,
            organizer_id=organizer_id,
            category=category,
            start_dt=start_dt,
            end_dt=end_dt,
            location=location,
            capacity=capacity,
            price=price,
            tags=tags or [],
        )
        self._repo.add(event)
        return event

    def get_event(self, event_id: str) -> Event:
        event = self._repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundError(event_id)
        return event

    def publish_event(self, event_id: str, by_user_id: str) -> Event:
        event = self.get_event(event_id)
        if event.organizer_id != by_user_id:
            raise InsufficientPermissionsError(by_user_id, "publish_event")
        if not event.publish():
            raise EventNotEditableError(event_id)
        self._repo.update(event)
        self._bus.publish(PlatformEvent.EVENT_PUBLISHED, {
            'event_id': event_id, 'title': event.title,
        })
        return event

    def cancel_event(self, event_id: str, by_user_id: str) -> Event:
        event = self.get_event(event_id)
        if event.organizer_id != by_user_id:
            raise InsufficientPermissionsError(by_user_id, "cancel_event")
        if not event.cancel():
            raise EventNotEditableError(event_id)
        self._repo.update(event)
        self._bus.publish(PlatformEvent.EVENT_CANCELLED, {
            'event_id': event_id, 'title': event.title,
        })
        return event

    def complete_event(self, event_id: str, by_user_id: str) -> Event:
        event = self.get_event(event_id)
        if event.organizer_id != by_user_id:
            raise InsufficientPermissionsError(by_user_id, "complete_event")
        if not event.complete():
            raise EventNotEditableError(event_id)
        self._repo.update(event)
        self._bus.publish(PlatformEvent.EVENT_COMPLETED, {
            'event_id': event_id,
        })
        return event

    def update_event(self, event_id: str, by_user_id: str, **kwargs) -> Event:
        event = self.get_event(event_id)
        if event.organizer_id != by_user_id:
            raise InsufficientPermissionsError(by_user_id, "update_event")
        if event.status not in (EventStatus.DRAFT, EventStatus.PUBLISHED):
            raise EventNotEditableError(event_id)
        for key, value in kwargs.items():
            if hasattr(event, key):
                setattr(event, key, value)
        self._repo.update(event)
        self._bus.publish(PlatformEvent.EVENT_UPDATED, {'event_id': event_id})
        return event

    def get_all_events(self) -> List[Event]:
        return self._sort.sort(self._repo.get_all())

    def get_available_events(self) -> List[Event]:
        return self._sort.sort(self._repo.find_available())

    def search_by_title(self, title: str) -> List[Event]:
        return self._sort.sort(self._repo.find_by_title(title))

    def get_by_category(self, category: EventCategory) -> List[Event]:
        return self._sort.sort(self._repo.find_by_category(category))

    def get_by_organizer(self, organizer_id: str) -> List[Event]:
        return self._repo.find_by_organizer(organizer_id)

    def set_sort_strategy(self, strategy: IEventSortStrategy) -> None:
        self._sort = strategy

    def get_statistics(self) -> dict:
        all_events = self._repo.get_all()
        return {
            'total': len(all_events),
            'published': sum(1 for e in all_events if e.status == EventStatus.PUBLISHED),
            'cancelled': sum(1 for e in all_events if e.status == EventStatus.CANCELLED),
            'completed': sum(1 for e in all_events if e.status == EventStatus.COMPLETED),
            'full': sum(1 for e in all_events if e.status == EventStatus.FULL),
            'draft': sum(1 for e in all_events if e.status == EventStatus.DRAFT),
        }
