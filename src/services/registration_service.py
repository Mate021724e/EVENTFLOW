from typing import List, Optional
from src.models.registration import Registration, RegistrationStatus
from src.models.event import EventStatus
from src.storage.interfaces import IRegistrationRepository, IEventRepository, IUserRepository
from src.services.observer import PlatformEventBus, PlatformEvent
from src.utils.id_generator import generate_registration_id, generate_ticket_number
from src.utils.exceptions import (
    EventNotFoundError, UserNotFoundError, RegistrationNotFoundError,
    EventNotAvailableError, UserBlockedError, RegistrationLimitExceededError,
    AlreadyRegisteredError, EventFullError,
)


class RegistrationService:
    def __init__(
        self,
        reg_repo: IRegistrationRepository,
        event_repo: IEventRepository,
        user_repo: IUserRepository,
        event_bus: Optional[PlatformEventBus] = None,
    ):
        self._registrations = reg_repo
        self._events = event_repo
        self._users = user_repo
        self._bus = event_bus or PlatformEventBus()

    def register(self, user_id: str, event_id: str) -> Registration:
        user = self._users.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        event = self._events.get_by_id(event_id)
        if not event:
            raise EventNotFoundError(event_id)
        if user.is_blocked():
            raise UserBlockedError(user_id, user.block_reason or '')
        if not user.can_register():
            raise RegistrationLimitExceededError(user_id)
        if event.status == EventStatus.CANCELLED:
            raise EventNotAvailableError(event_id)
        if event.status not in (EventStatus.PUBLISHED, EventStatus.FULL):
            raise EventNotAvailableError(event_id)

        existing = self._registrations.find_by_user_and_event(user_id, event_id)
        if existing:
            raise AlreadyRegisteredError(user_id, event_id)

        reg = Registration(
            id=generate_registration_id(),
            user_id=user_id,
            event_id=event_id,
        )

        if event.is_available():
            event.register_spot()
            self._events.update(event)
            ticket = generate_ticket_number()
            reg.confirm(ticket)
            self._bus.publish(PlatformEvent.REGISTRATION_CONFIRMED, {
                'user_id': user_id, 'event_id': event_id, 'registration_id': reg.id,
            })
            if event.status == EventStatus.FULL:
                self._bus.publish(PlatformEvent.EVENT_FULL, {'event_id': event_id})
        else:
            reg.add_to_waitlist()

        self._registrations.add(reg)
        user.add_registration(reg.id)
        self._users.update(user)
        return reg

    def cancel_registration(self, registration_id: str) -> Registration:
        reg = self._registrations.get_by_id(registration_id)
        if not reg:
            raise RegistrationNotFoundError(registration_id)

        was_confirmed = reg.status == RegistrationStatus.CONFIRMED

        if reg.cancel():
            user = self._users.get_by_id(reg.user_id)
            if user:
                user.remove_registration(registration_id)
                self._users.update(user)

            if was_confirmed:
                event = self._events.get_by_id(reg.event_id)
                if event:
                    event.unregister_spot()
                    self._events.update(event)

            self._registrations.update(reg)
            self._bus.publish(PlatformEvent.REGISTRATION_CANCELLED, {
                'registration_id': registration_id,
                'event_id': reg.event_id,
            })
            self._promote_from_waitlist(reg.event_id)
        return reg

    def check_in(self, registration_id: str) -> Registration:
        reg = self._registrations.get_by_id(registration_id)
        if not reg:
            raise RegistrationNotFoundError(registration_id)
        reg.check_in()
        self._registrations.update(reg)
        return reg

    def get_registration(self, registration_id: str) -> Registration:
        reg = self._registrations.get_by_id(registration_id)
        if not reg:
            raise RegistrationNotFoundError(registration_id)
        return reg

    def get_event_registrations(self, event_id: str) -> List[Registration]:
        return self._registrations.find_by_event(event_id)

    def get_user_registrations(self, user_id: str) -> List[Registration]:
        return self._registrations.find_by_user(user_id)

    def get_waitlist(self, event_id: str) -> List[Registration]:
        return self._registrations.find_waitlisted(event_id)

    def _promote_from_waitlist(self, event_id: str) -> None:
        event = self._events.get_by_id(event_id)
        if not event or not event.is_available():
            return
        waitlisted = self._registrations.find_waitlisted(event_id)
        if not waitlisted:
            return
        next_reg = sorted(waitlisted, key=lambda r: r.registered_at)[0]
        ticket = generate_ticket_number()
        if next_reg.promote_from_waitlist(ticket):
            event.register_spot()
            self._events.update(event)
            self._registrations.update(next_reg)
            user = self._users.get_by_id(next_reg.user_id)
            if user:
                user.add_registration(next_reg.id)
                self._users.update(user)
            self._bus.publish(PlatformEvent.WAITLIST_PROMOTED, {
                'registration_id': next_reg.id,
                'user_id': next_reg.user_id,
                'event_id': event_id,
            })

    def get_statistics(self, event_id: str) -> dict:
        all_regs = self._registrations.find_by_event(event_id)
        return {
            'total': len(all_regs),
            'confirmed': sum(1 for r in all_regs if r.status == RegistrationStatus.CONFIRMED),
            'pending': sum(1 for r in all_regs if r.status == RegistrationStatus.PENDING),
            'waitlisted': sum(1 for r in all_regs if r.status == RegistrationStatus.WAITLISTED),
            'cancelled': sum(1 for r in all_regs if r.status == RegistrationStatus.CANCELLED),
            'attended': sum(1 for r in all_regs if r.status == RegistrationStatus.ATTENDED),
        }
