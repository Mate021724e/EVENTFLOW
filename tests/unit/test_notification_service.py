import pytest
from src.models.notification import NotificationType
from src.storage.in_memory import (
    InMemoryNotificationRepository, InMemoryUserRepository, InMemoryEventRepository,
)
from src.services.notification_service import NotificationService


@pytest.fixture
def svc():
    return NotificationService(
        InMemoryNotificationRepository(),
        InMemoryUserRepository(),
        InMemoryEventRepository(),
    )


class TestSendNotification:
    def test_send_creates_notification(self, svc):
        n = svc.send('U1', NotificationType.EVENT_PUBLISHED, 'Title', 'Message', 'E1')
        assert n.id is not None
        assert n.user_id == 'U1'
        assert not n.read

    def test_send_without_event(self, svc):
        n = svc.send('U1', NotificationType.REGISTRATION_CONFIRMED, 'T', 'M')
        assert n.event_id is None


class TestGetNotifications:
    def test_get_user_notifications(self, svc):
        svc.send('U1', NotificationType.EVENT_PUBLISHED, 'T', 'M', 'E1')
        svc.send('U2', NotificationType.EVENT_PUBLISHED, 'T', 'M', 'E1')
        results = svc.get_user_notifications('U1')
        assert len(results) == 1

    def test_get_unread(self, svc):
        svc.send('U1', NotificationType.EVENT_PUBLISHED, 'T', 'M', 'E1')
        assert svc.unread_count('U1') == 1

    def test_mark_read(self, svc):
        n = svc.send('U1', NotificationType.EVENT_PUBLISHED, 'T', 'M', 'E1')
        svc.mark_read(n.id)
        assert svc.unread_count('U1') == 0

    def test_mark_all_read(self, svc):
        svc.send('U1', NotificationType.EVENT_PUBLISHED, 'T1', 'M', 'E1')
        svc.send('U1', NotificationType.EVENT_CANCELLED, 'T2', 'M', 'E1')
        count = svc.mark_all_read('U1')
        assert count == 2
        assert svc.unread_count('U1') == 0

    def test_unread_count_zero_initially(self, svc):
        assert svc.unread_count('U1') == 0

    def test_notify_event_registrants(self, svc):
        from src.models.registration import Registration, RegistrationStatus
        from src.utils.id_generator import generate_registration_id
        reg1 = Registration(id=generate_registration_id(), user_id='U1', event_id='E1')
        reg1.confirm('TKT-001')
        reg2 = Registration(id=generate_registration_id(), user_id='U2', event_id='E1')
        reg2.confirm('TKT-002')
        sent = svc.notify_event_registrants(
            'E1', NotificationType.EVENT_UPDATED, 'Updated', 'Details', [reg1, reg2]
        )
        assert len(sent) == 2

    def test_mark_read_missing_returns_none(self, svc):
        result = svc.mark_read('GHOST')
        assert result is None
