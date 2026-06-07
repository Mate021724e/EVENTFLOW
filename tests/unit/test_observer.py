import pytest
from src.services.observer import (
    PlatformEventBus, PlatformEvent, NotificationObserver,
    AuditObserver, WaitlistObserver,
)


class TestPlatformEventBus:
    def test_publish_notifies_subscriber(self):
        bus = PlatformEventBus()
        obs = NotificationObserver()
        bus.subscribe(PlatformEvent.EVENT_PUBLISHED, obs)
        bus.publish(PlatformEvent.EVENT_PUBLISHED, {'event_id': 'E1'})
        assert len(obs.get_received()) == 1

    def test_no_notification_without_subscription(self):
        bus = PlatformEventBus()
        obs = NotificationObserver()
        bus.publish(PlatformEvent.EVENT_PUBLISHED, {})
        assert len(obs.get_received()) == 0

    def test_unsubscribe_stops_notifications(self):
        bus = PlatformEventBus()
        obs = NotificationObserver()
        bus.subscribe(PlatformEvent.EVENT_PUBLISHED, obs)
        bus.unsubscribe(PlatformEvent.EVENT_PUBLISHED, obs)
        bus.publish(PlatformEvent.EVENT_PUBLISHED, {})
        assert len(obs.get_received()) == 0

    def test_multiple_observers(self):
        bus = PlatformEventBus()
        o1 = NotificationObserver()
        o2 = NotificationObserver()
        bus.subscribe(PlatformEvent.EVENT_CANCELLED, o1)
        bus.subscribe(PlatformEvent.EVENT_CANCELLED, o2)
        bus.publish(PlatformEvent.EVENT_CANCELLED, {'event_id': 'E1'})
        assert len(o1.get_received()) == 1
        assert len(o2.get_received()) == 1

    def test_event_log(self):
        bus = PlatformEventBus()
        bus.publish(PlatformEvent.EVENT_PUBLISHED, {})
        bus.publish(PlatformEvent.EVENT_CANCELLED, {})
        assert len(bus.get_event_log()) == 2

    def test_clear_log(self):
        bus = PlatformEventBus()
        bus.publish(PlatformEvent.EVENT_PUBLISHED, {})
        bus.clear_log()
        assert len(bus.get_event_log()) == 0

    def test_duplicate_subscribe_ignored(self):
        bus = PlatformEventBus()
        obs = NotificationObserver()
        bus.subscribe(PlatformEvent.EVENT_PUBLISHED, obs)
        bus.subscribe(PlatformEvent.EVENT_PUBLISHED, obs)
        bus.publish(PlatformEvent.EVENT_PUBLISHED, {})
        assert len(obs.get_received()) == 1

    def test_publish_no_data(self):
        bus = PlatformEventBus()
        obs = NotificationObserver()
        bus.subscribe(PlatformEvent.SPOT_FREED, obs)
        bus.publish(PlatformEvent.SPOT_FREED)
        assert len(obs.get_received()) == 1


class TestAuditObserver:
    def test_creates_log_entry(self):
        obs = AuditObserver()
        obs.on_event(PlatformEvent.EVENT_PUBLISHED, {'event_id': 'E1'})
        assert len(obs.get_log()) == 1
        assert 'event_published' in obs.get_log()[0]

    def test_multiple_entries(self):
        obs = AuditObserver()
        obs.on_event(PlatformEvent.EVENT_PUBLISHED, {})
        obs.on_event(PlatformEvent.REGISTRATION_CONFIRMED, {})
        assert len(obs.get_log()) == 2


class TestWaitlistObserver:
    def test_captures_promotion(self):
        obs = WaitlistObserver()
        obs.on_event(PlatformEvent.WAITLIST_PROMOTED, {'user_id': 'U1'})
        assert len(obs.get_promotions()) == 1

    def test_ignores_other_events(self):
        obs = WaitlistObserver()
        obs.on_event(PlatformEvent.EVENT_PUBLISHED, {})
        assert len(obs.get_promotions()) == 0

    def test_clear(self):
        obs = WaitlistObserver()
        obs.on_event(PlatformEvent.WAITLIST_PROMOTED, {})
        obs.clear()
        assert len(obs.get_promotions()) == 0
