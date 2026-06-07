import pytest
from datetime import datetime, timedelta
from src.models.event import Event, EventStatus, EventCategory
from src.services.sort_strategies import (
    SortByDateAscStrategy, SortByDateDescStrategy, SortByPopularityStrategy,
    SortByPriceAscStrategy, SortByPriceDescStrategy,
    SortByTitleStrategy, SortBySpotsLeftStrategy,
)


def make_event(id, title='T', start_offset_days=0, price=0.0, registered=0, capacity=100):
    now = datetime.now()
    e = Event(
        id=id, title=title, description='', organizer_id='U1',
        category=EventCategory.MEETUP,
        start_dt=now + timedelta(days=start_offset_days),
        end_dt=now + timedelta(days=start_offset_days + 1),
        location='Kyiv', capacity=capacity, price=price,
        registered_count=registered, status=EventStatus.PUBLISHED,
    )
    return e


@pytest.fixture
def events():
    return [
        make_event('E3', 'Alpha', start_offset_days=3, price=100.0, registered=50),
        make_event('E1', 'Gamma', start_offset_days=1, price=0.0, registered=10),
        make_event('E2', 'Beta',  start_offset_days=2, price=50.0, registered=80),
    ]


class TestSortByDateAsc:
    def test_sorted_ascending(self, events):
        result = SortByDateAscStrategy().sort(events)
        assert [e.id for e in result] == ['E1', 'E2', 'E3']

    def test_name(self):
        assert 'ascending' in SortByDateAscStrategy().get_name().lower()

    def test_empty_list(self):
        assert SortByDateAscStrategy().sort([]) == []

    def test_single_item(self, events):
        result = SortByDateAscStrategy().sort([events[0]])
        assert len(result) == 1


class TestSortByDateDesc:
    def test_sorted_descending(self, events):
        result = SortByDateDescStrategy().sort(events)
        assert [e.id for e in result] == ['E3', 'E2', 'E1']

    def test_name(self):
        assert 'descending' in SortByDateDescStrategy().get_name().lower()


class TestSortByPopularity:
    def test_most_registered_first(self, events):
        result = SortByPopularityStrategy().sort(events)
        assert result[0].id == 'E2'
        assert result[-1].id == 'E1'

    def test_name(self):
        assert SortByPopularityStrategy().get_name()


class TestSortByPriceAsc:
    def test_cheapest_first(self, events):
        result = SortByPriceAscStrategy().sort(events)
        assert result[0].price == 0.0
        assert result[-1].price == 100.0

    def test_name(self):
        assert 'ascending' in SortByPriceAscStrategy().get_name().lower()


class TestSortByPriceDesc:
    def test_most_expensive_first(self, events):
        result = SortByPriceDescStrategy().sort(events)
        assert result[0].price == 100.0
        assert result[-1].price == 0.0

    def test_name(self):
        assert 'descending' in SortByPriceDescStrategy().get_name().lower()


class TestSortByTitle:
    def test_alphabetical_order(self, events):
        result = SortByTitleStrategy().sort(events)
        assert result[0].title == 'Alpha'
        assert result[-1].title == 'Gamma'

    def test_name(self):
        assert SortByTitleStrategy().get_name()


class TestSortBySpotsLeft:
    def test_most_available_first(self):
        e1 = make_event('E1', capacity=100, registered=90)
        e2 = make_event('E2', capacity=100, registered=20)
        e3 = make_event('E3', capacity=100, registered=50)
        result = SortBySpotsLeftStrategy().sort([e1, e2, e3])
        assert result[0].id == 'E2'
        assert result[-1].id == 'E1'

    def test_name(self):
        assert SortBySpotsLeftStrategy().get_name()
