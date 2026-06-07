from datetime import datetime, date
from typing import List, Optional
from src.models.event import Event, EventCategory, EventStatus
from src.storage.interfaces import IEventRepository, IEventSortStrategy
from src.services.sort_strategies import SortByDateAscStrategy


class CalendarService:
    def __init__(
        self,
        event_repo: IEventRepository,
        sort_strategy: Optional[IEventSortStrategy] = None,
    ):
        self._repo = event_repo
        self._sort = sort_strategy or SortByDateAscStrategy()

    def get_events_on_date(self, target: date) -> List[Event]:
        result = [
            e for e in self._repo.get_all()
            if e.start_dt.date() == target
        ]
        return self._sort.sort(result)

    def get_events_in_range(self, start: datetime, end: datetime) -> List[Event]:
        result = [
            e for e in self._repo.get_all()
            if e.start_dt >= start and e.start_dt <= end
        ]
        return self._sort.sort(result)

    def get_upcoming_events(self, from_dt: Optional[datetime] = None) -> List[Event]:
        now = from_dt or datetime.now()
        result = [
            e for e in self._repo.get_all()
            if e.start_dt >= now
            and e.status in (EventStatus.PUBLISHED, EventStatus.FULL)
        ]
        return self._sort.sort(result)

    def get_events_by_month(self, year: int, month: int) -> List[Event]:
        result = [
            e for e in self._repo.get_all()
            if e.start_dt.year == year and e.start_dt.month == month
        ]
        return self._sort.sort(result)

    def get_free_events(self) -> List[Event]:
        result = [e for e in self._repo.get_all() if e.is_free() and e.is_available()]
        return self._sort.sort(result)

    def get_events_by_location(self, location: str) -> List[Event]:
        q = location.lower()
        result = [e for e in self._repo.get_all() if q in e.location.lower()]
        return self._sort.sort(result)

    def get_events_by_tag(self, tag: str) -> List[Event]:
        q = tag.lower()
        result = [e for e in self._repo.get_all() if any(q in t.lower() for t in e.tags)]
        return self._sort.sort(result)

    def get_events_by_price_range(self, min_price: float, max_price: float) -> List[Event]:
        result = [
            e for e in self._repo.get_all()
            if min_price <= e.price <= max_price
        ]
        return self._sort.sort(result)

    def set_sort_strategy(self, strategy: IEventSortStrategy) -> None:
        self._sort = strategy
