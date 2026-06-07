from typing import List, Optional
from src.models.user import User, UserRole, UserStatus
from src.storage.interfaces import IUserRepository
from src.utils.id_generator import generate_user_id
from src.utils.exceptions import (
    UserNotFoundError, DuplicateEmailError, InsufficientPermissionsError,
)


class UserService:
    def __init__(self, user_repo: IUserRepository):
        self._repo = user_repo

    def register_participant(self, name: str, email: str) -> User:
        if self._repo.find_by_email(email):
            raise DuplicateEmailError(email)
        user = User(id=generate_user_id(), name=name, email=email, role=UserRole.PARTICIPANT)
        return self._repo.add(user)

    def register_organizer(self, name: str, email: str) -> User:
        if self._repo.find_by_email(email):
            raise DuplicateEmailError(email)
        user = User(id=generate_user_id(), name=name, email=email, role=UserRole.ORGANIZER)
        return self._repo.add(user)

    def get_user(self, user_id: str) -> User:
        user = self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user

    def get_all_users(self) -> List[User]:
        return self._repo.get_all()

    def find_by_email(self, email: str) -> Optional[User]:
        return self._repo.find_by_email(email)

    def block_user(self, user_id: str, reason: str, by_admin_id: str) -> User:
        admin = self._repo.get_by_id(by_admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise InsufficientPermissionsError(by_admin_id, "block_user")
        user = self.get_user(user_id)
        user.block(reason)
        return self._repo.update(user)

    def unblock_user(self, user_id: str, by_admin_id: str) -> User:
        admin = self._repo.get_by_id(by_admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise InsufficientPermissionsError(by_admin_id, "unblock_user")
        user = self.get_user(user_id)
        user.unblock()
        return self._repo.update(user)

    def promote_to_organizer(self, user_id: str, by_admin_id: str) -> User:
        admin = self._repo.get_by_id(by_admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise InsufficientPermissionsError(by_admin_id, "promote_to_organizer")
        user = self.get_user(user_id)
        user.role = UserRole.ORGANIZER
        return self._repo.update(user)

    def get_statistics(self) -> dict:
        all_users = self._repo.get_all()
        return {
            'total': len(all_users),
            'active': sum(1 for u in all_users if u.status == UserStatus.ACTIVE),
            'blocked': sum(1 for u in all_users if u.status == UserStatus.BLOCKED),
            'participants': sum(1 for u in all_users if u.role == UserRole.PARTICIPANT),
            'organizers': sum(1 for u in all_users if u.role == UserRole.ORGANIZER),
            'admins': sum(1 for u in all_users if u.role == UserRole.ADMIN),
        }
