# Architecture

EventFlow is a pure in-memory event management platform with no external dependencies.

## Layers

```
src/
├── models/     Data classes. No business logic beyond state transitions.
├── services/   Business logic. Depends on interfaces only.
├── storage/    ABC interfaces + in-memory implementations.
└── utils/      ID generation, domain exceptions.
```

## Dependency flow

```
Service → IRepository (ABC) → InMemoryRepository
        → IEventSortStrategy  (Strategy pattern)
        → PlatformEventBus    (Observer pattern)
```

## Key rules

- Services receive interfaces via constructor injection.
- All repositories use `Dict[str, Model]` internally.

## Sort strategies

| Class | Behaviour |
|---|---|
| SortByDateAscStrategy | Earliest events first |
| SortByDateDescStrategy | Latest events first |
| SortByPopularityStrategy | Most registered first |
| SortByPriceAscStrategy | Cheapest first |
| SortByPriceDescStrategy | Most expensive first |
| SortByTitleStrategy | Alphabetical by title |
| SortBySpotsLeftStrategy | Most available spots first |

Switch at runtime: `event_service.set_sort_strategy(strategy)`.

## Business rules

| Rule | Value |
|---|---|
| Max registrations per user | 10 |
| Event capacity | Set at creation, must be > 0 |
| Waitlist | Automatic when event is full |
| Waitlist promotion | Automatic on cancellation |
