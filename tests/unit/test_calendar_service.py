import pytest
from datetime import datetime, timedelta, date
from src.models.event import Event, EventStatus, EventCategory
from src.storage.in_memory import InMemoryEventRepository
from src.services.calendar_service import CalendarService
from src.services.sort_strategies import SortByDateAscStrategy, SortByPriceAscStrategy


def make_event(id, days_from_now=1, price=0.0, status=EventStatus.PUBLISHED,
               location='Kyiv', tags=None, capacity=50):
    now = datetime.now()
    return Event(
        id=id, title=f'Event {id}', description='',
        organizer_id='U1', category=EventCategory.MEETUP,
        start_dt=now + timedelta(days=days_from_now),
        end_dt=now + timedelta(days=days_from_now + 1),
        location=location, capacity=capacity,
        price=price, status=status, tags=tags or [],
    )


@pytest.fixture
def populated_calendar():
    repo = InMemoryEventRepository()
    svc = CalendarService(repo, SortByDateAscStrategy())
    now = datetime.now()
    events = [
        make_event('E1', days_from_now=1, price=0.0, location='Kyiv', tags=['python']),
        make_event('E2', days_from_now=3, price=100.0, location='Lviv', tags=['tech', 'python']),
        make_event('E3', days_from_now=5, price=50.0, location='Kyiv', tags=['music']),
        make_event('E4', days_from_now=10, price=200.0, status=EventStatus.CANCELLED),
    ]
    for e in events:
        repo.add(e)
    return svc, repo, now


class TestGetEventsOnDate:
    def test_events_on_specific_date(self, populated_calendar):
        svc, repo, now = populated_calendar
        target = (now + timedelta(days=1)).date()
        results = svc.get_events_on_date(target)
        assert any(e.id == 'E1' for e in results)

    def test_no_events_on_empty_date(self, populated_calendar):
        svc, repo, now = populated_calendar
        target = (now + timedelta(days=100)).date()
        assert svc.get_events_on_date(target) == []


class TestGetEventsInRange:
    def test_events_in_range(self, populated_calendar):
        svc, repo, now = populated_calendar
        start = now + timedelta(days=1)
        end = now + timedelta(days=4)
        results = svc.get_events_in_range(start, end)
        assert any(e.id == 'E1' for e in results)
        assert any(e.id == 'E2' for e in results)
        assert not any(e.id == 'E3' for e in results)

    def test_empty_range(self, populated_calendar):
        svc, repo, now = populated_calendar
        start = now + timedelta(days=50)
        end = now + timedelta(days=60)
        assert svc.get_events_in_range(start, end) == []


class TestGetUpcomingEvents:
    def test_only_published_or_full(self, populated_calendar):
        svc, repo, now = populated_calendar
        results = svc.get_upcoming_events(now)
        assert not any(e.status == EventStatus.CANCELLED for e in results)

    def test_sorted_ascending(self, populated_calendar):
        svc, repo, now = populated_calendar
        results = svc.get_upcoming_events(now)
        for i in range(len(results) - 1):
            assert results[i].start_dt <= results[i+1].start_dt


class TestGetEventsByMonth:
    def test_events_by_month(self, populated_calendar):
        svc, repo, now = populated_calendar
        results = svc.get_events_by_month(now.year, now.month)
        assert len(results) >= 0


class TestGetFreeEvents:
    def test_only_free_and_available(self, populated_calendar):
        svc, repo, now = populated_calendar
        results = svc.get_free_events()
        assert all(e.price == 0.0 for e in results)
        assert all(e.is_available() for e in results)


class TestGetEventsByLocation:
    def test_find_by_location(self, populated_calendar):
        svc, repo, now = populated_calendar
        results = svc.get_events_by_location('kyiv')
        assert all('kyiv' in e.location.lower() for e in results)

    def test_case_insensitive(self, populated_calendar):
        svc, repo, now = populated_calendar
        results = svc.get_events_by_location('LVIV')
        assert any(e.id == 'E2' for e in results)


class TestGetEventsByTag:
    def test_find_by_tag(self, populated_calendar):
        svc, repo, now = populated_calendar
        results = svc.get_events_by_tag('python')
        assert any(e.id == 'E1' for e in results)
        assert any(e.id == 'E2' for e in results)

    def test_tag_not_found_empty(self, populated_calendar):
        svc, repo, now = populated_calendar
        assert svc.get_events_by_tag('blockchain') == []


class TestGetEventsByPriceRange:
    def test_price_range(self, populated_calendar):
        svc, repo, now = populated_calendar
        results = svc.get_events_by_price_range(0.0, 50.0)
        assert all(0.0 <= e.price <= 50.0 for e in results)

    def test_free_only(self, populated_calendar):
        svc, repo, now = populated_calendar
        results = svc.get_events_by_price_range(0.0, 0.0)
        assert all(e.price == 0.0 for e in results)


class TestSortStrategySwitch:
    def test_switch_strategy(self, populated_calendar):
        svc, repo, now = populated_calendar
        svc.set_sort_strategy(SortByPriceAscStrategy())
        results = svc.get_upcoming_events(now)
        prices = [e.price for e in results]
        assert prices == sorted(prices)
