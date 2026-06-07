import pytest
from datetime import datetime, timedelta
from src.storage.in_memory import (
    InMemoryEventRepository, InMemoryUserRepository,
    InMemoryRegistrationRepository, InMemoryNotificationRepository,
)
from src.models.event import Event, EventStatus, EventCategory
from src.models.user import User, UserRole, UserStatus
from src.models.registration import Registration, RegistrationStatus
from src.models.notification import Notification, NotificationType


def event(id='E1', **kw):
    now = datetime.now()
    d = dict(
        id=id, title='T', description='', organizer_id='U1',
        category=EventCategory.MEETUP,
        start_dt=now + timedelta(days=1), end_dt=now + timedelta(days=2),
        location='Kyiv', capacity=50, status=EventStatus.PUBLISHED,
    )
    d.update(kw)
    return Event(**d)

def user(id='U1', **kw):
    d = dict(id=id, name='Test', email=f'{id}@t.com', role=UserRole.PARTICIPANT)
    d.update(kw)
    return User(**d)

def reg(id='R1', **kw):
    d = dict(id=id, user_id='U1', event_id='E1', registered_at=datetime.now())
    d.update(kw)
    return Registration(**d)

def notif(id='N1', **kw):
    d = dict(
        id=id, user_id='U1', event_id='E1',
        type=NotificationType.EVENT_PUBLISHED, title='T', message='M',
    )
    d.update(kw)
    return Notification(**d)


class TestEventRepository:
    def test_add_and_get(self):
        repo = InMemoryEventRepository()
        e = repo.add(event())
        assert repo.get_by_id('E1') == e

    def test_get_missing_none(self):
        assert InMemoryEventRepository().get_by_id('X') is None

    def test_get_all(self):
        repo = InMemoryEventRepository()
        repo.add(event('E1'))
        repo.add(event('E2'))
        assert len(repo.get_all()) == 2

    def test_update(self):
        repo = InMemoryEventRepository()
        e = repo.add(event())
        e.title = 'Updated'
        repo.update(e)
        assert repo.get_by_id('E1').title == 'Updated'

    def test_delete(self):
        repo = InMemoryEventRepository()
        repo.add(event())
        assert repo.delete('E1') is True
        assert repo.get_by_id('E1') is None

    def test_delete_missing(self):
        assert InMemoryEventRepository().delete('X') is False

    def test_find_by_organizer(self):
        repo = InMemoryEventRepository()
        repo.add(event('E1', organizer_id='U1'))
        repo.add(event('E2', organizer_id='U2'))
        assert len(repo.find_by_organizer('U1')) == 1

    def test_find_by_category(self):
        repo = InMemoryEventRepository()
        repo.add(event('E1', category=EventCategory.CONFERENCE))
        repo.add(event('E2', category=EventCategory.MEETUP))
        assert len(repo.find_by_category(EventCategory.CONFERENCE)) == 1

    def test_find_available(self):
        repo = InMemoryEventRepository()
        repo.add(event('E1', status=EventStatus.PUBLISHED))
        repo.add(event('E2', status=EventStatus.CANCELLED))
        assert len(repo.find_available()) == 1

    def test_find_by_title_partial(self):
        repo = InMemoryEventRepository()
        repo.add(event('E1', title='Python Conference'))
        assert len(repo.find_by_title('python')) == 1

    def test_clear_and_count(self):
        repo = InMemoryEventRepository()
        repo.add(event())
        repo.clear()
        assert repo.count() == 0


class TestUserRepository:
    def test_add_and_get(self):
        repo = InMemoryUserRepository()
        u = repo.add(user())
        assert repo.get_by_id('U1') == u

    def test_find_by_email(self):
        repo = InMemoryUserRepository()
        repo.add(user(email='unique@test.com'))
        assert repo.find_by_email('unique@test.com') is not None

    def test_find_active(self):
        repo = InMemoryUserRepository()
        u1 = user('U1')
        u2 = user('U2', email='u2@t.com')
        u2.block('reason')
        repo.add(u1)
        repo.add(u2)
        assert len(repo.find_active()) == 1

    def test_find_blocked(self):
        repo = InMemoryUserRepository()
        u = user()
        u.block('reason')
        repo.add(u)
        assert len(repo.find_blocked()) == 1

    def test_delete(self):
        repo = InMemoryUserRepository()
        repo.add(user())
        assert repo.delete('U1') is True
        assert repo.get_by_id('U1') is None


class TestRegistrationRepository:
    def test_add_and_get(self):
        repo = InMemoryRegistrationRepository()
        r = repo.add(reg())
        assert repo.get_by_id('R1') == r

    def test_find_by_user(self):
        repo = InMemoryRegistrationRepository()
        repo.add(reg('R1', user_id='U1'))
        repo.add(reg('R2', user_id='U2'))
        assert len(repo.find_by_user('U1')) == 1

    def test_find_by_event(self):
        repo = InMemoryRegistrationRepository()
        repo.add(reg('R1', event_id='E1'))
        repo.add(reg('R2', event_id='E2'))
        assert len(repo.find_by_event('E1')) == 1

    def test_find_active_by_event(self):
        repo = InMemoryRegistrationRepository()
        r1 = reg('R1')
        r2 = reg('R2')
        r2.cancel()
        repo.add(r1)
        repo.add(r2)
        assert len(repo.find_active_by_event('E1')) == 1

    def test_find_waitlisted(self):
        repo = InMemoryRegistrationRepository()
        r = reg()
        r.add_to_waitlist()
        repo.add(r)
        assert len(repo.find_waitlisted('E1')) == 1

    def test_find_by_user_and_event(self):
        repo = InMemoryRegistrationRepository()
        repo.add(reg())
        found = repo.find_by_user_and_event('U1', 'E1')
        assert found is not None

    def test_find_by_user_and_event_cancelled_not_found(self):
        repo = InMemoryRegistrationRepository()
        r = reg()
        r.cancel()
        repo.add(r)
        assert repo.find_by_user_and_event('U1', 'E1') is None


class TestNotificationRepository:
    def test_add_and_get(self):
        repo = InMemoryNotificationRepository()
        n = repo.add(notif())
        assert repo.get_by_id('N1') == n

    def test_find_by_user(self):
        repo = InMemoryNotificationRepository()
        repo.add(notif('N1', user_id='U1'))
        repo.add(notif('N2', user_id='U2'))
        assert len(repo.find_by_user('U1')) == 1

    def test_find_unread(self):
        repo = InMemoryNotificationRepository()
        n1 = notif('N1')
        n2 = notif('N2')
        n2.mark_read()
        repo.add(n1)
        repo.add(n2)
        assert len(repo.find_unread_by_user('U1')) == 1
