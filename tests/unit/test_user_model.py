import pytest
from src.models.user import User, UserRole, UserStatus
from datetime import datetime


def make_user(**kw):
    d = dict(id='U1', name='Olena', email='olena@test.com', role=UserRole.PARTICIPANT)
    d.update(kw)
    return User(**d)


class TestUserCreation:
    def test_default_status_active(self):
        u = make_user()
        assert u.status == UserStatus.ACTIVE

    def test_default_empty_registrations(self):
        u = make_user()
        assert u.registrations == []

    def test_default_empty_organized_events(self):
        u = make_user()
        assert u.organized_events == []

    def test_is_active(self):
        u = make_user()
        assert u.is_active() is True

    def test_is_not_blocked_by_default(self):
        u = make_user()
        assert u.is_blocked() is False


class TestUserCanRegister:
    def test_active_user_can_register(self):
        u = make_user()
        assert u.can_register() is True

    def test_blocked_user_cannot_register(self):
        u = make_user()
        u.block("violation")
        assert u.can_register() is False

    def test_user_at_max_registrations_cannot_register(self):
        u = make_user()
        u.registrations = [str(i) for i in range(u.MAX_REGISTRATIONS)]
        assert u.can_register() is False


class TestUserCanOrganize:
    def test_organizer_can_organize(self):
        u = make_user(role=UserRole.ORGANIZER)
        assert u.can_organize() is True

    def test_participant_cannot_organize(self):
        u = make_user(role=UserRole.PARTICIPANT)
        assert u.can_organize() is False

    def test_admin_can_organize(self):
        u = make_user(role=UserRole.ADMIN)
        assert u.can_organize() is True

    def test_blocked_organizer_cannot_organize(self):
        u = make_user(role=UserRole.ORGANIZER)
        u.block("test")
        assert u.can_organize() is False


class TestUserBlock:
    def test_block_sets_status(self):
        u = make_user()
        u.block("spam")
        assert u.status == UserStatus.BLOCKED

    def test_block_sets_reason(self):
        u = make_user()
        u.block("spam")
        assert u.block_reason == "spam"

    def test_block_sets_timestamp(self):
        u = make_user()
        u.block("test")
        assert u.blocked_at is not None

    def test_unblock_restores_active(self):
        u = make_user()
        u.block("test")
        u.unblock()
        assert u.status == UserStatus.ACTIVE

    def test_unblock_clears_reason(self):
        u = make_user()
        u.block("test")
        u.unblock()
        assert u.block_reason is None


class TestUserRegistrations:
    def test_add_registration(self):
        u = make_user()
        u.add_registration('R1')
        assert 'R1' in u.registrations

    def test_add_duplicate_ignored(self):
        u = make_user()
        u.add_registration('R1')
        u.add_registration('R1')
        assert u.registrations.count('R1') == 1

    def test_remove_registration(self):
        u = make_user()
        u.add_registration('R1')
        u.remove_registration('R1')
        assert 'R1' not in u.registrations

    def test_remove_nonexistent_safe(self):
        u = make_user()
        u.remove_registration('GHOST')

    def test_add_organized_event(self):
        u = make_user(role=UserRole.ORGANIZER)
        u.add_organized_event('E1')
        assert 'E1' in u.organized_events


class TestUserEquality:
    def test_equal_by_id(self):
        u1 = make_user(id='X')
        u2 = make_user(id='X')
        assert u1 == u2

    def test_not_equal_different_id(self):
        assert make_user(id='A') != make_user(id='B')

    def test_hashable(self):
        u = make_user()
        assert u in {u}
