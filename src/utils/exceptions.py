class EventFlowError(Exception):
    pass

class EventNotFoundError(EventFlowError):
    def __init__(self, event_id: str):
        self.event_id = event_id
        super().__init__(f"Event not found: {event_id}")

class UserNotFoundError(EventFlowError):
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User not found: {user_id}")

class RegistrationNotFoundError(EventFlowError):
    def __init__(self, reg_id: str):
        self.reg_id = reg_id
        super().__init__(f"Registration not found: {reg_id}")

class EventNotAvailableError(EventFlowError):
    def __init__(self, event_id: str):
        super().__init__(f"Event is not available for registration: {event_id}")

class EventFullError(EventFlowError):
    def __init__(self, event_id: str):
        super().__init__(f"Event is full: {event_id}")

class UserBlockedError(EventFlowError):
    def __init__(self, user_id: str, reason: str = ''):
        super().__init__(f"User is blocked: {user_id}. Reason: {reason}")

class RegistrationLimitExceededError(EventFlowError):
    def __init__(self, user_id: str):
        super().__init__(f"Registration limit exceeded for user: {user_id}")

class AlreadyRegisteredError(EventFlowError):
    def __init__(self, user_id: str, event_id: str):
        super().__init__(f"User {user_id} is already registered for event {event_id}")

class DuplicateEmailError(EventFlowError):
    def __init__(self, email: str):
        super().__init__(f"User with email already exists: {email}")

class InsufficientPermissionsError(EventFlowError):
    def __init__(self, user_id: str, action: str):
        super().__init__(f"User {user_id} lacks permission for: {action}")

class InvalidEventDatesError(EventFlowError):
    def __init__(self, msg: str = ''):
        super().__init__(f"Invalid event dates: {msg}")

class EventNotEditableError(EventFlowError):
    def __init__(self, event_id: str):
        super().__init__(f"Event cannot be edited in current state: {event_id}")
