import pytest
from datetime import datetime, timedelta
from src.models.event import EventStatus, EventCategory
from src.utils.exceptions import (
    EventNotFoundError, InsufficientPermissionsError,
    InvalidEventDatesError, EventNotEditableError,
)


class TestCreateEvent:
    def test_create_success(self, event_service, sample_organizer, future_dt, far_future_dt):
        e = event_service.create_event(
            'Meetup', 'Desc', sample_organizer.id, EventCategory.MEETUP,
            future_dt, far_future_dt, 'Kyiv', 50,
        )
        assert e.id is not None
        assert e.status == EventStatus.DRAFT

    def test_end_before_start_raises(self, event_service, sample_organizer, future_dt):
        with pytest.raises(InvalidEventDatesError):
            event_service.create_event(
                'Bad', '', sample_organizer.id, EventCategory.MEETUP,
                future_dt, future_dt - timedelta(hours=1), 'Kyiv', 10,
            )

    def test_equal_start_end_raises(self, event_service, sample_organizer, future_dt):
        with pytest.raises(InvalidEventDatesError):
            event_service.create_event(
                'Bad', '', sample_organizer.id, EventCategory.MEETUP,
                future_dt, future_dt, 'Kyiv', 10,
            )

    def test_zero_capacity_raises(self, event_service, sample_organizer, future_dt, far_future_dt):
        with pytest.raises(InvalidEventDatesError):
            event_service.create_event(
                'Bad', '', sample_organizer.id, EventCategory.MEETUP,
                future_dt, far_future_dt, 'Kyiv', 0,
            )

    def test_with_tags(self, event_service, sample_organizer, future_dt, far_future_dt):
        e = event_service.create_event(
            'Tag Event', '', sample_organizer.id, EventCategory.MEETUP,
            future_dt, far_future_dt, 'Kyiv', 10, tags=['python', 'tech'],
        )
        assert 'python' in e.tags


class TestPublishEvent:
    def test_publish_by_organizer(self, event_service, sample_organizer, future_dt, far_future_dt):
        e = event_service.create_event(
            'E', '', sample_organizer.id, EventCategory.MEETUP,
            future_dt, far_future_dt, 'Kyiv', 10,
        )
        published = event_service.publish_event(e.id, sample_organizer.id)
        assert published.status == EventStatus.PUBLISHED

    def test_publish_by_wrong_user_raises(self, event_service, sample_organizer, sample_participant, future_dt, far_future_dt):
        e = event_service.create_event(
            'E', '', sample_organizer.id, EventCategory.MEETUP,
            future_dt, far_future_dt, 'Kyiv', 10,
        )
        with pytest.raises(InsufficientPermissionsError):
            event_service.publish_event(e.id, sample_participant.id)

    def test_publish_missing_event_raises(self, event_service, sample_organizer):
        with pytest.raises(EventNotFoundError):
            event_service.publish_event('GHOST', sample_organizer.id)

    def test_publish_already_published_raises(self, event_service, sample_organizer, future_dt, far_future_dt):
        e = event_service.create_event(
            'E', '', sample_organizer.id, EventCategory.MEETUP,
            future_dt, far_future_dt, 'Kyiv', 10,
        )
        event_service.publish_event(e.id, sample_organizer.id)
        with pytest.raises(EventNotEditableError):
            event_service.publish_event(e.id, sample_organizer.id)


class TestCancelEvent:
    def test_cancel_by_organizer(self, event_service, sample_event, sample_organizer):
        cancelled = event_service.cancel_event(sample_event.id, sample_organizer.id)
        assert cancelled.status == EventStatus.CANCELLED

    def test_cancel_wrong_user_raises(self, event_service, sample_event, sample_participant):
        with pytest.raises(InsufficientPermissionsError):
            event_service.cancel_event(sample_event.id, sample_participant.id)

    def test_cancel_completed_raises(self, event_service, sample_event, sample_organizer):
        event_service.complete_event(sample_event.id, sample_organizer.id)
        with pytest.raises(EventNotEditableError):
            event_service.cancel_event(sample_event.id, sample_organizer.id)


class TestCompleteEvent:
    def test_complete_published(self, event_service, sample_event, sample_organizer):
        completed = event_service.complete_event(sample_event.id, sample_organizer.id)
        assert completed.status == EventStatus.COMPLETED

    def test_complete_wrong_user_raises(self, event_service, sample_event, sample_participant):
        with pytest.raises(InsufficientPermissionsError):
            event_service.complete_event(sample_event.id, sample_participant.id)


class TestUpdateEvent:
    def test_update_title(self, event_service, sample_event, sample_organizer):
        updated = event_service.update_event(sample_event.id, sample_organizer.id, title='New Title')
        assert updated.title == 'New Title'

    def test_update_wrong_user_raises(self, event_service, sample_event, sample_participant):
        with pytest.raises(InsufficientPermissionsError):
            event_service.update_event(sample_event.id, sample_participant.id, title='Hack')

    def test_update_cancelled_raises(self, event_service, sample_event, sample_organizer):
        event_service.cancel_event(sample_event.id, sample_organizer.id)
        with pytest.raises(EventNotEditableError):
            event_service.update_event(sample_event.id, sample_organizer.id, title='X')


class TestSearchEvents:
    def test_search_by_title(self, event_service, sample_event):
        results = event_service.search_by_title('pycon')
        assert len(results) >= 1

    def test_get_by_category(self, event_service, sample_event):
        results = event_service.get_by_category(EventCategory.CONFERENCE)
        assert any(e.id == sample_event.id for e in results)

    def test_get_available(self, event_service, sample_event):
        results = event_service.get_available_events()
        assert any(e.id == sample_event.id for e in results)

    def test_get_by_organizer(self, event_service, sample_event, sample_organizer):
        results = event_service.get_by_organizer(sample_organizer.id)
        assert any(e.id == sample_event.id for e in results)


class TestEventStats:
    def test_statistics(self, event_service, sample_event):
        stats = event_service.get_statistics()
        assert stats['total'] >= 1
        assert stats['published'] >= 1


class TestSortStrategySwitch:
    def test_set_sort_strategy(self, event_service, sample_event):
        from src.services.sort_strategies import SortByPriceAscStrategy
        event_service.set_sort_strategy(SortByPriceAscStrategy())
        results = event_service.get_all_events()
        assert isinstance(results, list)
