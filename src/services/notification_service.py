from typing import List, Optional
from src.models.notification import Notification, NotificationType
from src.storage.interfaces import INotificationRepository, IUserRepository, IEventRepository
from src.utils.id_generator import generate_notification_id
from src.utils.exceptions import UserNotFoundError


class NotificationService:
    def __init__(
        self,
        notif_repo: INotificationRepository,
        user_repo: IUserRepository,
        event_repo: IEventRepository,
    ):
        self._repo = notif_repo
        self._users = user_repo
        self._events = event_repo

    def send(
        self,
        user_id: str,
        notif_type: NotificationType,
        title: str,
        message: str,
        event_id: Optional[str] = None,
    ) -> Notification:
        notif = Notification(
            id=generate_notification_id(),
            user_id=user_id,
            event_id=event_id,
            type=notif_type,
            title=title,
            message=message,
        )
        return self._repo.add(notif)

    def notify_event_registrants(
        self,
        event_id: str,
        notif_type: NotificationType,
        title: str,
        message: str,
        registrations: list,
    ) -> List[Notification]:
        sent = []
        user_ids = {r.user_id for r in registrations if r.is_active()}
        for uid in user_ids:
            notif = self.send(uid, notif_type, title, message, event_id)
            sent.append(notif)
        return sent

    def get_user_notifications(self, user_id: str) -> List[Notification]:
        return self._repo.find_by_user(user_id)

    def get_unread(self, user_id: str) -> List[Notification]:
        return self._repo.find_unread_by_user(user_id)

    def mark_read(self, notif_id: str) -> Optional[Notification]:
        notif = self._repo.get_by_id(notif_id)
        if notif:
            notif.mark_read()
            self._repo.add(notif)
        return notif

    def mark_all_read(self, user_id: str) -> int:
        unread = self._repo.find_unread_by_user(user_id)
        for n in unread:
            n.mark_read()
            self._repo.add(n)
        return len(unread)

    def unread_count(self, user_id: str) -> int:
        return len(self._repo.find_unread_by_user(user_id))
