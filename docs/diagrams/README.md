# UML diagrams

## Use cases

**Actors:** Participant, Organizer, Admin

### Participant
- Search and browse events
- View event details and calendar
- Register for an event
- Cancel registration
- Join waitlist (automatic when full)
- Check-in at the event
- View notifications

### Organizer (includes all Participant actions)
- Create an event
- Publish an event
- Cancel an event
- Complete an event
- Update event details
- View registrations and statistics

### Admin (includes all Organizer actions)
- Block / unblock users
- Promote participants to organizers

---

## Domain model

```
Event                       Registration               User
───────────────────         ───────────────────        ───────────────────
id                          id                         id
title                       user_id  ─────────────→    name
description                 event_id ─────────────→    email
organizer_id                registered_at              role: PARTICIPANT
category                    status: PENDING             | ORGANIZER | ADMIN
start_dt                      | CONFIRMED              status: ACTIVE | BLOCKED
end_dt                        | WAITLISTED             registrations[]
location                      | ATTENDED               organized_events[]
capacity                      | CANCELLED
registered_count            ticket_number
price                       checked_in
status: DRAFT | PUBLISHED
  | FULL | CANCELLED
  | COMPLETED
tags[]

Notification
───────────────────
id
user_id  ─────────────→ User
event_id ─────────────→ Event
type
title / message
read / read_at
```

---

## Class relationships

```
IEventRepository (ABC)
    └── InMemoryEventRepository

IUserRepository (ABC)
    └── InMemoryUserRepository

IRegistrationRepository (ABC)
    └── InMemoryRegistrationRepository

INotificationRepository (ABC)
    └── InMemoryNotificationRepository

IEventSortStrategy (ABC)          ← Strategy
    ├── SortByDateAscStrategy
    ├── SortByDateDescStrategy
    ├── SortByPopularityStrategy
    ├── SortByPriceAscStrategy
    ├── SortByPriceDescStrategy
    ├── SortByTitleStrategy
    └── SortBySpotsLeftStrategy

IPlatformObserver (ABC)           ← Observer
    ├── NotificationObserver
    ├── AuditObserver
    └── WaitlistObserver

PlatformEventBus
    ├── subscribe(event, observer)
    └── publish(event, data)
```

---

## Waitlist algorithm

1. When an event reaches capacity → status becomes FULL.
2. A new registration for a FULL event → added as WAITLISTED.
3. When a confirmed registration is cancelled:
   - The freed spot is returned to the event.
   - `_promote_from_waitlist` runs automatically.
   - The earliest waitlisted registration is promoted to CONFIRMED.
   - `WAITLIST_PROMOTED` event is published to all observers.
