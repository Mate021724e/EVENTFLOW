# Testing strategy

## Stack
- pytest — test runner
- pytest-cov — coverage

## Running

```bash
pip install -r requirements.txt
mkdir -p reports
pytest
```

## Layout

```
tests/
├── conftest.py          shared fixtures
├── unit/                one file per source module
└── integration/         cross-service scenarios
```

## Reports

- `reports/junit.xml`    for SonarQube
- `reports/coverage.xml` for SonarQube
- `reports/htmlcov/`     visual line-by-line report

## Guidelines

1. Write tests first.
2. Each method: happy path + edge case + error path minimum.
3. Use fixtures from conftest.py; do not instantiate repos directly in tests.
