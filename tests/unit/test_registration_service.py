import pytest
from datetime import datetime, timedelta
from src.models.registration import RegistrationStatus
from src.models.event import EventStatus, EventCategory
from src.services.observer import PlatformEvent, NotificationObserver
from src.storage.in_memory import (
    InMemoryEventRepository, InMemoryUserRepository, InMemoryRegistrationRepository,
)
from src.services.event_service import EventService
from src.services.user_service import UserService
from src.services.registration_service import RegistrationService
from src.services.sort_strategies import SortByDateAscStrategy
from src.services.observer import PlatformEventBus
from src.utils.exceptions import (
    UserNotFoundError, EventNotFoundError, RegistrationNotFoundError,
    UserBlockedError, RegistrationLimitExceededError,
    AlreadyRegisteredError, EventNotAvailableError,
)


@pytest.fixture
def setup():
    event_repo = InMemoryEventRepository()
    user_repo = InMemoryUserRepository()
    reg_repo = InMemoryRegistrationRepository()
    bus = PlatformEventBus()
    event_svc = EventService(event_repo, SortByDateAscStrategy(), bus)
    user_svc = UserService(user_repo)
    reg_svc = RegistrationService(reg_repo, event_repo, user_repo, bus)
    now = datetime.now()
    organizer = user_svc.register_organizer('Organizer', 'org@test.com')
    participant = user_svc.register_participant('Participant', 'part@test.com')
    event = event_svc.create_event(
        'Test Event', 'Desc', organizer.id, EventCategory.MEETUP,
        now + timedelta(days=1), now + timedelta(days=2), 'Kyiv', 5,
    )
    event_svc.publish_event(event.id, organizer.id)
    return {
        'event_svc': event_svc, 'user_svc': user_svc, 'reg_svc': reg_svc,
        'bus': bus, 'organizer': organizer, 'participant': participant,
        'event': event, 'event_repo': event_repo, 'user_repo': user_repo,
        'reg_repo': reg_repo,
    }


class TestRegister:
    def test_register_success(self, setup):
        s = setup
        reg = s['reg_svc'].register(s['participant'].id, s['event'].id)
        assert reg.status == RegistrationStatus.CONFIRMED
        assert reg.ticket_number is not None

    def test_register_decrements_spots(self, setup):
        s = setup
        s['reg_svc'].register(s['participant'].id, s['event'].id)
        event = s['event_repo'].get_by_id(s['event'].id)
        assert event.spots_left() == 4

    def test_register_adds_to_user(self, setup):
        s = setup
        reg = s['reg_svc'].register(s['participant'].id, s['event'].id)
        user = s['user_repo'].get_by_id(s['participant'].id)
        assert reg.id in user.registrations

    def test_register_missing_user_raises(self, setup):
        s = setup
        with pytest.raises(UserNotFoundError):
            s['reg_svc'].register('GHOST', s['event'].id)

    def test_register_missing_event_raises(self, setup):
        s = setup
        with pytest.raises(EventNotFoundError):
            s['reg_svc'].register(s['participant'].id, 'GHOST')

    def test_register_blocked_user_raises(self, setup):
        s = setup
        s['participant'].block('test')
        s['user_repo'].update(s['participant'])
        with pytest.raises(UserBlockedError):
            s['reg_svc'].register(s['participant'].id, s['event'].id)

    def test_register_twice_raises(self, setup):
        s = setup
        s['reg_svc'].register(s['participant'].id, s['event'].id)
        with pytest.raises(AlreadyRegisteredError):
            s['reg_svc'].register(s['participant'].id, s['event'].id)

    def test_register_cancelled_event_raises(self, setup):
        s = setup
        s['event_svc'].cancel_event(s['event'].id, s['organizer'].id)
        with pytest.raises(EventNotAvailableError):
            s['reg_svc'].register(s['participant'].id, s['event'].id)

    def test_register_draft_event_raises(self, setup):
        s = setup
        now = datetime.now()
        draft = s['event_svc'].create_event(
            'Draft', '', s['organizer'].id, EventCategory.MEETUP,
            now + timedelta(days=1), now + timedelta(days=2), 'Kyiv', 5,
        )
        with pytest.raises(EventNotAvailableError):
            s['reg_svc'].register(s['participant'].id, draft.id)

    def test_register_full_event_goes_to_waitlist(self, setup):
        s = setup
        now = datetime.now()
        small_event = s['event_svc'].create_event(
            'Small', '', s['organizer'].id, EventCategory.MEETUP,
            now + timedelta(days=1), now + timedelta(days=2), 'Kyiv', 1,
        )
        s['event_svc'].publish_event(small_event.id, s['organizer'].id)
        p2 = s['user_svc'].register_participant('P2', 'p2@test.com')
        s['reg_svc'].register(s['participant'].id, small_event.id)
        reg2 = s['reg_svc'].register(p2.id, small_event.id)
        assert reg2.status == RegistrationStatus.WAITLISTED

    def test_register_publishes_event(self, setup):
        s = setup
        obs = NotificationObserver()
        s['bus'].subscribe(PlatformEvent.REGISTRATION_CONFIRMED, obs)
        s['reg_svc'].register(s['participant'].id, s['event'].id)
        assert len(obs.get_received()) == 1

    def test_registration_limit_exceeded_raises(self, setup):
        s = setup
        s['participant'].registrations = [str(i) for i in range(s['participant'].MAX_REGISTRATIONS)]
        s['user_repo'].update(s['participant'])
        with pytest.raises(RegistrationLimitExceededError):
            s['reg_svc'].register(s['participant'].id, s['event'].id)


class TestCancelRegistration:
    def test_cancel_success(self, setup):
        s = setup
        reg = s['reg_svc'].register(s['participant'].id, s['event'].id)
        cancelled = s['reg_svc'].cancel_registration(reg.id)
        assert cancelled.status == RegistrationStatus.CANCELLED

    def test_cancel_restores_spot(self, setup):
        s = setup
        reg = s['reg_svc'].register(s['participant'].id, s['event'].id)
        before = s['event_repo'].get_by_id(s['event'].id).spots_left()
        s['reg_svc'].cancel_registration(reg.id)
        after = s['event_repo'].get_by_id(s['event'].id).spots_left()
        assert after > before

    def test_cancel_removes_from_user(self, setup):
        s = setup
        reg = s['reg_svc'].register(s['participant'].id, s['event'].id)
        s['reg_svc'].cancel_registration(reg.id)
        user = s['user_repo'].get_by_id(s['participant'].id)
        assert reg.id not in user.registrations

    def test_cancel_missing_raises(self, setup):
        s = setup
        with pytest.raises(RegistrationNotFoundError):
            s['reg_svc'].cancel_registration('GHOST')

    def test_cancel_promotes_waitlist(self, setup):
        s = setup
        now = datetime.now()
        small = s['event_svc'].create_event(
            'Small', '', s['organizer'].id, EventCategory.MEETUP,
            now + timedelta(days=1), now + timedelta(days=2), 'Kyiv', 1,
        )
        s['event_svc'].publish_event(small.id, s['organizer'].id)
        p2 = s['user_svc'].register_participant('P2', 'p2@test.com')
        reg1 = s['reg_svc'].register(s['participant'].id, small.id)
        reg2 = s['reg_svc'].register(p2.id, small.id)
        assert reg2.status == RegistrationStatus.WAITLISTED
        s['reg_svc'].cancel_registration(reg1.id)
        updated = s['reg_repo'].get_by_id(reg2.id)
        assert updated.status == RegistrationStatus.CONFIRMED


class TestCheckIn:
    def test_check_in_confirmed(self, setup):
        s = setup
        reg = s['reg_svc'].register(s['participant'].id, s['event'].id)
        checked = s['reg_svc'].check_in(reg.id)
        assert checked.checked_in is True
        assert checked.status == RegistrationStatus.ATTENDED

    def test_check_in_missing_raises(self, setup):
        s = setup
        with pytest.raises(RegistrationNotFoundError):
            s['reg_svc'].check_in('GHOST')


class TestStatistics:
    def test_statistics(self, setup):
        s = setup
        s['reg_svc'].register(s['participant'].id, s['event'].id)
        stats = s['reg_svc'].get_statistics(s['event'].id)
        assert stats['total'] == 1
        assert stats['confirmed'] == 1
