# EventFlow

An in-memory event management platform supporting event creation, participant registration, waitlist management, notifications, and a filterable calendar.

[![CI](https://github.com/YOUR_USERNAME/eventflow/actions/workflows/ci-pipeline.yml/badge.svg)](https://github.com/YOUR_USERNAME/eventflow/actions/workflows/ci-pipeline.yml)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=eventflow&metric=coverage)](https://sonarcloud.io/project/overview?id=eventflow)
[![Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=eventflow&metric=alert_status)](https://sonarcloud.io/project/overview?id=eventflow)

## Quick start

```bash
pip install -r requirements.txt
mkdir -p reports
python -m pytest
open reports/htmlcov/index.html
```

## Docker

```bash
docker build -t eventflow .
docker run --rm -v $(pwd)/reports:/app/reports eventflow
```

## Project structure

```
eventflow/
├── src/
│   ├── models/         Event, User, Registration, Notification
│   ├── services/
│   │   ├── event_service.py
│   │   ├── user_service.py
│   │   ├── registration_service.py
│   │   ├── notification_service.py
│   │   ├── calendar_service.py
│   │   ├── sort_strategies.py   Strategy pattern — 7 sort algorithms
│   │   └── observer.py          Observer pattern — event bus
│   ├── storage/        Repository interfaces + in-memory implementations
│   └── utils/          ID generator, domain exceptions
├── tests/
│   ├── unit/           model, service and repository tests
│   └── integration/    cross-service workflow tests
├── docs/diagrams/      UML descriptions
├── .cursor/rules/      architecture and testing guides
├── .github/workflows/  CI pipeline
├── .cursorrules
├── Dockerfile
├── pytest.ini
└── sonar-project.properties
```

## Design patterns

**Strategy** — event sort/filter algorithms, switchable at runtime:

```python
event_service.set_sort_strategy(SortByPopularityStrategy())
calendar_service.set_sort_strategy(SortByPriceAscStrategy())
```

**Observer** — platform event bus:

```python
bus.subscribe(PlatformEvent.WAITLIST_PROMOTED, my_observer)
bus.subscribe(PlatformEvent.EVENT_CANCELLED, audit_observer)
```

## Business rules

| Rule | Value |
|---|---|
| Max registrations per user | 10 |
| Waitlist | Automatic when event is full |
| Waitlist promotion | Automatic on cancellation (earliest first) |
| Roles | Participant, Organizer, Admin |

## CI/CD

Every push triggers:
1. Install dependencies
2. Run tests → generate `reports/junit.xml`, `reports/coverage.xml`, `reports/htmlcov/`
3. Upload reports as downloadable artifacts (30-day retention)
4. Send results to SonarCloud

Add `SONAR_TOKEN` secret and update `sonar.projectKey` to enable SonarCloud.
