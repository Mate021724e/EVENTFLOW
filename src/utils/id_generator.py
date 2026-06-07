import uuid


def generate_id(prefix: str = '') -> str:
    uid = str(uuid.uuid4())
    return f'{prefix}{uid}' if prefix else uid

def generate_event_id() -> str:
    return generate_id('EVT-')

def generate_user_id() -> str:
    return generate_id('USR-')

def generate_registration_id() -> str:
    return generate_id('REG-')

def generate_notification_id() -> str:
    return generate_id('NTF-')

def generate_ticket_number() -> str:
    return generate_id('TKT-')
