import pytest
from src.models.registration import Registration, RegistrationStatus
from datetime import datetime


def make_reg(**kw):
    d = dict(id='R1', user_id='U1', event_id='E1')
    d.update(kw)
    return Registration(**d)


class TestRegistrationCreation:
    def test_default_status_pending(self):
        r = make_reg()
        assert r.status == RegistrationStatus.PENDING

    def test_not_checked_in_by_default(self):
        r = make_reg()
        assert r.checked_in is False

    def test_is_active_when_pending(self):
        r = make_reg()
        assert r.is_active() is True


class TestRegistrationConfirm:
    def test_confirm_from_pending(self):
        r = make_reg()
        assert r.confirm('TKT-001') is True
        assert r.status == RegistrationStatus.CONFIRMED
        assert r.ticket_number == 'TKT-001'

    def test_confirm_already_confirmed_fails(self):
        r = make_reg()
        r.confirm('TKT-001')
        assert r.confirm('TKT-002') is False

    def test_confirm_waitlisted_fails(self):
        r = make_reg()
        r.add_to_waitlist()
        assert r.confirm('TKT-001') is False


class TestRegistrationCancel:
    def test_cancel_pending(self):
        r = make_reg()
        assert r.cancel() is True
        assert r.status == RegistrationStatus.CANCELLED
        assert r.cancelled_at is not None

    def test_cancel_confirmed(self):
        r = make_reg()
        r.confirm('TKT-001')
        assert r.cancel() is True

    def test_cancel_waitlisted(self):
        r = make_reg()
        r.add_to_waitlist()
        assert r.cancel() is True

    def test_cancel_already_cancelled_fails(self):
        r = make_reg()
        r.cancel()
        assert r.cancel() is False

    def test_cancelled_not_active(self):
        r = make_reg()
        r.cancel()
        assert r.is_active() is False


class TestRegistrationCheckIn:
    def test_check_in_confirmed(self):
        r = make_reg()
        r.confirm('TKT-001')
        assert r.check_in() is True
        assert r.checked_in is True
        assert r.status == RegistrationStatus.ATTENDED
        assert r.checked_in_at is not None

    def test_check_in_pending_fails(self):
        r = make_reg()
        assert r.check_in() is False

    def test_check_in_twice_fails(self):
        r = make_reg()
        r.confirm('TKT-001')
        r.check_in()
        assert r.check_in() is False


class TestWaitlist:
    def test_add_to_waitlist(self):
        r = make_reg()
        assert r.add_to_waitlist() is True
        assert r.status == RegistrationStatus.WAITLISTED

    def test_add_confirmed_to_waitlist_fails(self):
        r = make_reg()
        r.confirm('TKT-001')
        assert r.add_to_waitlist() is False

    def test_promote_from_waitlist(self):
        r = make_reg()
        r.add_to_waitlist()
        assert r.promote_from_waitlist('TKT-002') is True
        assert r.status == RegistrationStatus.CONFIRMED
        assert r.ticket_number == 'TKT-002'

    def test_promote_not_waitlisted_fails(self):
        r = make_reg()
        assert r.promote_from_waitlist('TKT-001') is False


class TestRegistrationEquality:
    def test_equal_by_id(self):
        r1 = make_reg(id='X')
        r2 = make_reg(id='X')
        assert r1 == r2

    def test_hashable(self):
        r = make_reg()
        assert r in {r}
