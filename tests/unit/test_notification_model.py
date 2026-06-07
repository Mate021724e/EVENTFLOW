import pytest
from src.models.notification import Notification, NotificationType
from datetime import datetime


def make_notif(**kw):
    d = dict(
        id='N1', user_id='U1', event_id='E1',
        type=NotificationType.EVENT_PUBLISHED,
        title='Title', message='Message',
    )
    d.update(kw)
    return Notification(**d)


class TestNotificationCreation:
    def test_not_read_by_default(self):
        n = make_notif()
        assert n.read is False

    def test_read_at_none_by_default(self):
        n = make_notif()
        assert n.read_at is None

    def test_event_id_optional(self):
        n = make_notif(event_id=None)
        assert n.event_id is None


class TestNotificationMarkRead:
    def test_mark_read(self):
        n = make_notif()
        n.mark_read()
        assert n.read is True
        assert n.read_at is not None

    def test_mark_read_twice_safe(self):
        n = make_notif()
        n.mark_read()
        first_read_at = n.read_at
        n.mark_read()
        assert n.read_at == first_read_at

    def test_equality(self):
        n1 = make_notif(id='X')
        n2 = make_notif(id='X')
        assert n1 == n2

    def test_hashable(self):
        n = make_notif()
        assert n in {n}
