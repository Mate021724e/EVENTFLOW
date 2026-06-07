import pytest
from datetime import datetime, timedelta
from src.storage.in_memory import (
    InMemoryEventRepository, InMemoryUserRepository,
    InMemoryRegistrationRepository, InMemoryNotificationRepository,
)
from src.services.event_service import EventService
from src.services.user_service import UserService
from src.services.registration_service import RegistrationService
from src.services.notification_service import NotificationService
from src.services.calendar_service import CalendarService
from src.services.sort_strategies import SortByDateAscStrategy
from src.services.observer import PlatformEventBus
from src.models.event import EventCategory


@pytest.fixture
def event_repo():
    return InMemoryEventRepository()

@pytest.fixture
def user_repo():
    return InMemoryUserRepository()

@pytest.fixture
def reg_repo():
    return InMemoryRegistrationRepository()

@pytest.fixture
def notif_repo():
    return InMemoryNotificationRepository()

@pytest.fixture
def bus():
    return PlatformEventBus()

@pytest.fixture
def event_service(event_repo, bus):
    return EventService(event_repo, SortByDateAscStrategy(), bus)

@pytest.fixture
def user_service(user_repo):
    return UserService(user_repo)

@pytest.fixture
def reg_service(reg_repo, event_repo, user_repo, bus):
    return RegistrationService(reg_repo, event_repo, user_repo, bus)

@pytest.fixture
def notif_service(notif_repo, user_repo, event_repo):
    return NotificationService(notif_repo, user_repo, event_repo)

@pytest.fixture
def calendar_service(event_repo):
    return CalendarService(event_repo, SortByDateAscStrategy())

@pytest.fixture
def future_dt():
    return datetime.now() + timedelta(days=7)

@pytest.fixture
def far_future_dt():
    return datetime.now() + timedelta(days=30)

@pytest.fixture
def sample_organizer(user_service):
    return user_service.register_organizer("Ivan Kovalenko", "ivan@eventflow.io")

@pytest.fixture
def sample_participant(user_service):
    return user_service.register_participant("Olena Shevchenko", "olena@eventflow.io")

@pytest.fixture
def sample_event(event_service, sample_organizer, future_dt, far_future_dt):
    event = event_service.create_event(
        title="PyCon Ukraine",
        description="Annual Python conference",
        organizer_id=sample_organizer.id,
        category=EventCategory.CONFERENCE,
        start_dt=future_dt,
        end_dt=far_future_dt,
        location="Kyiv, Ukraine",
        capacity=100,
        price=500.0,
        tags=["python", "technology"],
    )
    event_service.publish_event(event.id, sample_organizer.id)
    return event
