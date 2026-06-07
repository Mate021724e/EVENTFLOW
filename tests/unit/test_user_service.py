import pytest
from src.models.user import UserRole, UserStatus
from src.utils.exceptions import (
    UserNotFoundError, DuplicateEmailError, InsufficientPermissionsError,
)
from src.storage.in_memory import InMemoryUserRepository
from src.services.user_service import UserService


@pytest.fixture
def svc():
    return UserService(InMemoryUserRepository())

@pytest.fixture
def admin(svc):
    from src.models.user import User, UserRole
    from src.utils.id_generator import generate_user_id
    u = User(id=generate_user_id(), name='Admin', email='admin@test.com', role=UserRole.ADMIN)
    svc._repo.add(u)
    return u


class TestRegisterUser:
    def test_register_participant(self, svc):
        u = svc.register_participant('Alice', 'alice@test.com')
        assert u.role == UserRole.PARTICIPANT

    def test_register_organizer(self, svc):
        u = svc.register_organizer('Bob', 'bob@test.com')
        assert u.role == UserRole.ORGANIZER

    def test_duplicate_email_raises(self, svc):
        svc.register_participant('Alice', 'dup@test.com')
        with pytest.raises(DuplicateEmailError):
            svc.register_participant('Alice2', 'dup@test.com')

    def test_generated_id(self, svc):
        u = svc.register_participant('Alice', 'a@t.com')
        assert u.id


class TestGetUser:
    def test_get_existing(self, svc):
        u = svc.register_participant('Alice', 'a@t.com')
        assert svc.get_user(u.id) == u

    def test_get_missing_raises(self, svc):
        with pytest.raises(UserNotFoundError):
            svc.get_user('GHOST')


class TestBlockUser:
    def test_block_by_admin(self, svc, admin):
        u = svc.register_participant('Alice', 'a@t.com')
        blocked = svc.block_user(u.id, 'spam', admin.id)
        assert blocked.status == UserStatus.BLOCKED

    def test_block_by_non_admin_raises(self, svc):
        u1 = svc.register_participant('Alice', 'a@t.com')
        u2 = svc.register_participant('Bob', 'b@t.com')
        with pytest.raises(InsufficientPermissionsError):
            svc.block_user(u1.id, 'test', u2.id)

    def test_unblock_by_admin(self, svc, admin):
        u = svc.register_participant('Alice', 'a@t.com')
        svc.block_user(u.id, 'test', admin.id)
        unblocked = svc.unblock_user(u.id, admin.id)
        assert unblocked.status == UserStatus.ACTIVE


class TestPromoteToOrganizer:
    def test_promote_by_admin(self, svc, admin):
        u = svc.register_participant('Alice', 'a@t.com')
        promoted = svc.promote_to_organizer(u.id, admin.id)
        assert promoted.role == UserRole.ORGANIZER

    def test_promote_by_non_admin_raises(self, svc):
        u1 = svc.register_participant('Alice', 'a@t.com')
        u2 = svc.register_participant('Bob', 'b@t.com')
        with pytest.raises(InsufficientPermissionsError):
            svc.promote_to_organizer(u1.id, u2.id)


class TestStatistics:
    def test_statistics(self, svc, admin):
        svc.register_participant('A', 'a@t.com')
        svc.register_organizer('B', 'b@t.com')
        stats = svc.get_statistics()
        assert stats['total'] == 3
        assert stats['admins'] == 1
        assert stats['participants'] == 1
        assert stats['organizers'] == 1
