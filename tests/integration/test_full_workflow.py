import pytest
from datetime import datetime, timedelta
from src.storage.in_memory import (
    InMemoryEventRepository, InMemoryUserRepository,
    InMemoryRegistrationRepository, InMemoryNotificationRepository,
)
from src.services.event_service import EventService
from src.services.user_service import UserService
from src.services.registration_service import RegistrationService
from src.services.notification_service import NotificationService
from src.services.calendar_service import CalendarService
from src.services.sort_strategies import SortByDateAscStrategy, SortByPopularityStrategy
from src.services.observer import PlatformEventBus, PlatformEvent, NotificationObserver, WaitlistObserver
from src.models.event import EventCategory, EventStatus
from src.models.registration import RegistrationStatus
from src.models.notification import NotificationType


@pytest.fixture
def platform():
    event_repo = InMemoryEventRepository()
    user_repo = InMemoryUserRepository()
    reg_repo = InMemoryRegistrationRepository()
    notif_repo = InMemoryNotificationRepository()
    bus = PlatformEventBus()
    return {
        'events': EventService(event_repo, SortByDateAscStrategy(), bus),
        'users': UserService(user_repo),
        'registrations': RegistrationService(reg_repo, event_repo, user_repo, bus),
        'notifications': NotificationService(notif_repo, user_repo, event_repo),
        'calendar': CalendarService(event_repo, SortByDateAscStrategy()),
        'bus': bus,
        'event_repo': event_repo,
        'user_repo': user_repo,
        'reg_repo': reg_repo,
    }


def future(days=7):
    return datetime.now() + timedelta(days=days)


class TestEventLifecycle:
    def test_create_publish_complete(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Ivan', 'ivan@test.com')
        event = p['events'].create_event(
            'PyCon', 'Python conf', organizer.id, EventCategory.CONFERENCE,
            future(7), future(8), 'Kyiv', 200, price=300.0,
        )
        assert event.status == EventStatus.DRAFT
        p['events'].publish_event(event.id, organizer.id)
        assert p['event_repo'].get_by_id(event.id).status == EventStatus.PUBLISHED
        p['events'].complete_event(event.id, organizer.id)
        assert p['event_repo'].get_by_id(event.id).status == EventStatus.COMPLETED

    def test_create_publish_cancel_notifies(self, platform):
        p = platform
        obs = NotificationObserver()
        p['bus'].subscribe(PlatformEvent.EVENT_PUBLISHED, obs)
        p['bus'].subscribe(PlatformEvent.EVENT_CANCELLED, obs)
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        event = p['events'].create_event(
            'Cancelled Conf', '', organizer.id, EventCategory.CONFERENCE,
            future(3), future(4), 'Odesa', 50,
        )
        p['events'].publish_event(event.id, organizer.id)
        p['events'].cancel_event(event.id, organizer.id)
        assert len(obs.get_received()) == 2

    def test_update_published_event(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        event = p['events'].create_event(
            'Workshop', '', organizer.id, EventCategory.WORKSHOP,
            future(5), future(6), 'Lviv', 30,
        )
        p['events'].publish_event(event.id, organizer.id)
        updated = p['events'].update_event(event.id, organizer.id, title='Advanced Workshop')
        assert updated.title == 'Advanced Workshop'


class TestRegistrationWorkflow:
    def test_register_confirm_checkin(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        participant = p['users'].register_participant('User', 'user@test.com')
        event = p['events'].create_event(
            'Meetup', '', organizer.id, EventCategory.MEETUP,
            future(2), future(3), 'Kyiv', 10,
        )
        p['events'].publish_event(event.id, organizer.id)
        reg = p['registrations'].register(participant.id, event.id)
        assert reg.status == RegistrationStatus.CONFIRMED
        checked = p['registrations'].check_in(reg.id)
        assert checked.status == RegistrationStatus.ATTENDED

    def test_waitlist_promotion_on_cancel(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        p1 = p['users'].register_participant('P1', 'p1@test.com')
        p2 = p['users'].register_participant('P2', 'p2@test.com')
        event = p['events'].create_event(
            'Small', '', organizer.id, EventCategory.MEETUP,
            future(1), future(2), 'Kyiv', 1,
        )
        p['events'].publish_event(event.id, organizer.id)
        reg1 = p['registrations'].register(p1.id, event.id)
        reg2 = p['registrations'].register(p2.id, event.id)
        assert reg2.status == RegistrationStatus.WAITLISTED
        p['registrations'].cancel_registration(reg1.id)
        updated = p['reg_repo'].get_by_id(reg2.id)
        assert updated.status == RegistrationStatus.CONFIRMED

    def test_waitlist_observer_fires(self, platform):
        p = platform
        obs = WaitlistObserver()
        p['bus'].subscribe(PlatformEvent.WAITLIST_PROMOTED, obs)
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        p1 = p['users'].register_participant('P1', 'p1@test.com')
        p2 = p['users'].register_participant('P2', 'p2@test.com')
        event = p['events'].create_event(
            'Tiny', '', organizer.id, EventCategory.MEETUP,
            future(1), future(2), 'Kyiv', 1,
        )
        p['events'].publish_event(event.id, organizer.id)
        reg1 = p['registrations'].register(p1.id, event.id)
        p['registrations'].register(p2.id, event.id)
        p['registrations'].cancel_registration(reg1.id)
        assert len(obs.get_promotions()) == 1

    def test_full_event_fires_event(self, platform):
        p = platform
        obs = NotificationObserver()
        p['bus'].subscribe(PlatformEvent.EVENT_FULL, obs)
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        participant = p['users'].register_participant('P', 'p@test.com')
        event = p['events'].create_event(
            'Tiny2', '', organizer.id, EventCategory.MEETUP,
            future(1), future(2), 'Kyiv', 1,
        )
        p['events'].publish_event(event.id, organizer.id)
        p['registrations'].register(participant.id, event.id)
        assert len(obs.get_received()) == 1

    def test_multiple_registrations_stats(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        event = p['events'].create_event(
            'Big', '', organizer.id, EventCategory.CONFERENCE,
            future(5), future(6), 'Kyiv', 50,
        )
        p['events'].publish_event(event.id, organizer.id)
        for i in range(5):
            participant = p['users'].register_participant(f'P{i}', f'p{i}@test.com')
            p['registrations'].register(participant.id, event.id)
        stats = p['registrations'].get_statistics(event.id)
        assert stats['confirmed'] == 5
        assert stats['total'] == 5


class TestCalendarIntegration:
    def test_calendar_shows_upcoming(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        event = p['events'].create_event(
            'Future Event', '', organizer.id, EventCategory.WEBINAR,
            future(3), future(4), 'Online', 100,
        )
        p['events'].publish_event(event.id, organizer.id)
        upcoming = p['calendar'].get_upcoming_events()
        assert any(e.id == event.id for e in upcoming)

    def test_calendar_excludes_cancelled(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        event = p['events'].create_event(
            'Cancelled', '', organizer.id, EventCategory.CONCERT,
            future(2), future(3), 'Kharkiv', 200,
        )
        p['events'].publish_event(event.id, organizer.id)
        p['events'].cancel_event(event.id, organizer.id)
        upcoming = p['calendar'].get_upcoming_events()
        assert not any(e.id == event.id for e in upcoming)

    def test_calendar_filter_by_location(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        e1 = p['events'].create_event('E1', '', organizer.id, EventCategory.MEETUP,
                                       future(1), future(2), 'Kyiv', 50)
        e2 = p['events'].create_event('E2', '', organizer.id, EventCategory.MEETUP,
                                       future(1), future(2), 'Lviv', 50)
        p['events'].publish_event(e1.id, organizer.id)
        p['events'].publish_event(e2.id, organizer.id)
        kyiv_events = p['calendar'].get_events_by_location('Kyiv')
        assert any(e.id == e1.id for e in kyiv_events)
        assert not any(e.id == e2.id for e in kyiv_events)

    def test_calendar_filter_by_tag(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        event = p['events'].create_event(
            'Python Day', '', organizer.id, EventCategory.CONFERENCE,
            future(4), future(5), 'Kyiv', 50, tags=['python', 'open-source'],
        )
        p['events'].publish_event(event.id, organizer.id)
        results = p['calendar'].get_events_by_tag('python')
        assert any(e.id == event.id for e in results)

    def test_calendar_price_range(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        e_free = p['events'].create_event('Free', '', organizer.id, EventCategory.MEETUP,
                                           future(1), future(2), 'Kyiv', 50, price=0.0)
        e_paid = p['events'].create_event('Paid', '', organizer.id, EventCategory.CONFERENCE,
                                           future(2), future(3), 'Kyiv', 50, price=500.0)
        p['events'].publish_event(e_free.id, organizer.id)
        p['events'].publish_event(e_paid.id, organizer.id)
        free = p['calendar'].get_free_events()
        assert any(e.id == e_free.id for e in free)
        assert not any(e.id == e_paid.id for e in free)


class TestSortStrategySwitch:
    def test_switch_to_popularity(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        e1 = p['events'].create_event('E1', '', organizer.id, EventCategory.MEETUP,
                                       future(1), future(2), 'Kyiv', 50)
        e2 = p['events'].create_event('E2', '', organizer.id, EventCategory.MEETUP,
                                       future(2), future(3), 'Kyiv', 50)
        p['events'].publish_event(e1.id, organizer.id)
        p['events'].publish_event(e2.id, organizer.id)
        for i in range(3):
            user = p['users'].register_participant(f'U{i}', f'u{i}@test.com')
            p['registrations'].register(user.id, e2.id)
        p['events'].set_sort_strategy(SortByPopularityStrategy())
        results = p['events'].get_all_events()
        assert results[0].id == e2.id

    def test_user_admin_workflow(self, platform):
        p = platform
        from src.models.user import User, UserRole
        from src.utils.id_generator import generate_user_id
        admin = User(id=generate_user_id(), name='Admin', email='admin@ef.io', role=UserRole.ADMIN)
        p['user_repo'].add(admin)
        user = p['users'].register_participant('Bob', 'bob@test.com')
        p['users'].block_user(user.id, 'violation', admin.id)
        assert p['user_repo'].get_by_id(user.id).is_blocked()
        promoted = p['users'].promote_to_organizer(user.id, admin.id)
        assert promoted.role == UserRole.ORGANIZER


class TestNotificationIntegration:
    def test_send_bulk_to_registrants(self, platform):
        p = platform
        organizer = p['users'].register_organizer('Org', 'org@test.com')
        event = p['events'].create_event(
            'Bulk Test', '', organizer.id, EventCategory.WEBINAR,
            future(5), future(6), 'Online', 20,
        )
        p['events'].publish_event(event.id, organizer.id)
        users = [p['users'].register_participant(f'U{i}', f'u{i}@bulk.com') for i in range(3)]
        regs = [p['registrations'].register(u.id, event.id) for u in users]
        sent = p['notifications'].notify_event_registrants(
            event.id, NotificationType.EVENT_UPDATED, 'Update', 'Details changed', regs
        )
        assert len(sent) == 3
        for u in users:
            assert p['notifications'].unread_count(u.id) == 1

    def test_mark_all_read(self, platform):
        p = platform
        for i in range(3):
            p['notifications'].send(
                'U1', NotificationType.EVENT_REMINDER, f'Reminder {i}', 'Dont forget', 'E1'
            )
        assert p['notifications'].unread_count('U1') == 3
        p['notifications'].mark_all_read('U1')
        assert p['notifications'].unread_count('U1') == 0
