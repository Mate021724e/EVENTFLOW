import pytest
from datetime import datetime, timedelta
from src.models.event import Event, EventStatus, EventCategory


def make_event(**kw):
    now = datetime.now()
    d = dict(
        id='E1', title='Test', description='Desc', organizer_id='U1',
        category=EventCategory.CONFERENCE,
        start_dt=now + timedelta(days=1),
        end_dt=now + timedelta(days=2),
        location='Kyiv', capacity=50,
    )
    d.update(kw)
    return Event(**d)


class TestEventCreation:
    def test_default_status_draft(self):
        e = make_event()
        assert e.status == EventStatus.DRAFT

    def test_default_price_zero(self):
        e = make_event()
        assert e.price == 0.0

    def test_default_registered_count_zero(self):
        e = make_event()
        assert e.registered_count == 0

    def test_is_free_when_price_zero(self):
        e = make_event(price=0.0)
        assert e.is_free() is True

    def test_not_free_when_price_set(self):
        e = make_event(price=100.0)
        assert e.is_free() is False

    def test_spots_left_equals_capacity_initially(self):
        e = make_event(capacity=30)
        assert e.spots_left() == 30

    def test_repr_contains_id_and_title(self):
        e = make_event()
        assert 'E1' in repr(e)
        assert 'Test' in repr(e)


class TestEventAvailability:
    def test_draft_event_not_available(self):
        e = make_event()
        assert e.is_available() is False

    def test_published_event_available(self):
        e = make_event()
        e.publish()
        assert e.is_available() is True

    def test_cancelled_event_not_available(self):
        e = make_event()
        e.publish()
        e.cancel()
        assert e.is_available() is False

    def test_full_event_not_available(self):
        e = make_event(capacity=1)
        e.publish()
        e.register_spot()
        assert e.is_available() is False


class TestEventPublish:
    def test_publish_draft_succeeds(self):
        e = make_event()
        assert e.publish() is True
        assert e.status == EventStatus.PUBLISHED

    def test_publish_already_published_fails(self):
        e = make_event()
        e.publish()
        assert e.publish() is False

    def test_publish_cancelled_fails(self):
        e = make_event()
        e.publish()
        e.cancel()
        assert e.publish() is False


class TestEventCancel:
    def test_cancel_draft_succeeds(self):
        e = make_event()
        assert e.cancel() is True
        assert e.status == EventStatus.CANCELLED

    def test_cancel_published_succeeds(self):
        e = make_event()
        e.publish()
        assert e.cancel() is True

    def test_cancel_completed_fails(self):
        e = make_event()
        e.publish()
        e.complete()
        assert e.cancel() is False

    def test_cancel_already_cancelled_fails(self):
        e = make_event()
        e.cancel()
        assert e.cancel() is False


class TestEventComplete:
    def test_complete_published_succeeds(self):
        e = make_event()
        e.publish()
        assert e.complete() is True
        assert e.status == EventStatus.COMPLETED

    def test_complete_full_succeeds(self):
        e = make_event(capacity=1)
        e.publish()
        e.register_spot()
        assert e.complete() is True

    def test_complete_draft_fails(self):
        e = make_event()
        assert e.complete() is False


class TestEventRegistration:
    def test_register_spot_decrements_available(self):
        e = make_event(capacity=3)
        e.publish()
        e.register_spot()
        assert e.spots_left() == 2
        assert e.registered_count == 1

    def test_last_spot_sets_full_status(self):
        e = make_event(capacity=1)
        e.publish()
        e.register_spot()
        assert e.status == EventStatus.FULL

    def test_register_when_full_fails(self):
        e = make_event(capacity=1)
        e.publish()
        e.register_spot()
        assert e.register_spot() is False

    def test_unregister_restores_published_status(self):
        e = make_event(capacity=1)
        e.publish()
        e.register_spot()
        e.unregister_spot()
        assert e.status == EventStatus.PUBLISHED
        assert e.spots_left() == 1

    def test_unregister_when_zero_registered_safe(self):
        e = make_event()
        e.publish()
        e.unregister_spot()
        assert e.registered_count == 0


class TestEventDuration:
    def test_duration_hours(self):
        now = datetime.now()
        e = make_event(start_dt=now, end_dt=now + timedelta(hours=3))
        assert e.duration_hours() == 3.0

    def test_duration_fractional(self):
        now = datetime.now()
        e = make_event(start_dt=now, end_dt=now + timedelta(minutes=90))
        assert e.duration_hours() == 1.5


class TestEventEquality:
    def test_equal_by_id(self):
        e1 = make_event(id='X')
        e2 = make_event(id='X')
        assert e1 == e2

    def test_not_equal_different_id(self):
        assert make_event(id='A') != make_event(id='B')

    def test_hashable(self):
        e = make_event()
        assert e in {e}

    def test_not_equal_to_non_event(self):
        assert make_event() != "not an event"
