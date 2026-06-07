from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class RegistrationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    WAITLISTED = "waitlisted"
    ATTENDED = "attended"


@dataclass
class Registration:
    id: str
    user_id: str
    event_id: str
    registered_at: datetime = field(default_factory=datetime.now)
    status: RegistrationStatus = RegistrationStatus.PENDING
    ticket_number: Optional[str] = None
    checked_in: bool = False
    checked_in_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    notes: str = ""

    def confirm(self, ticket_number: str) -> bool:
        if self.status == RegistrationStatus.PENDING:
            self.status = RegistrationStatus.CONFIRMED
            self.ticket_number = ticket_number
            return True
        return False

    def cancel(self) -> bool:
        if self.status in (RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED,
                           RegistrationStatus.WAITLISTED):
            self.status = RegistrationStatus.CANCELLED
            self.cancelled_at = datetime.now()
            return True
        return False

    def check_in(self) -> bool:
        if self.status == RegistrationStatus.CONFIRMED and not self.checked_in:
            self.checked_in = True
            self.checked_in_at = datetime.now()
            self.status = RegistrationStatus.ATTENDED
            return True
        return False

    def add_to_waitlist(self) -> bool:
        if self.status == RegistrationStatus.PENDING:
            self.status = RegistrationStatus.WAITLISTED
            return True
        return False

    def promote_from_waitlist(self, ticket_number: str) -> bool:
        if self.status == RegistrationStatus.WAITLISTED:
            self.status = RegistrationStatus.CONFIRMED
            self.ticket_number = ticket_number
            return True
        return False

    def is_active(self) -> bool:
        return self.status in (
            RegistrationStatus.PENDING,
            RegistrationStatus.CONFIRMED,
            RegistrationStatus.WAITLISTED,
        )

    def __eq__(self, other):
        return isinstance(other, Registration) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"Registration(id={self.id!r}, user_id={self.user_id!r}, event_id={self.event_id!r})"
