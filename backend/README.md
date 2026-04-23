# Backend Bootstrap

This directory contains the Django backend bootstrap for AVK. The backend is structured as a modular monolith so that product domains can evolve independently without introducing premature service boundaries.

## What Exists in Phase 0

- Django project configuration with environment-based settings
- Django REST Framework baseline configuration
- PostgreSQL, Celery, and Redis placeholders
- modular app packages under `apps/`
- minimal health and service-info API endpoints
- audit, permission, and sensitive-access abstractions
- pytest, Ruff, and Black configuration

## What Does Not Exist Yet

- production domain models
- workflow orchestration
- payment provider integrations
- moderation queues
- support routing logic

## App Structure

Each domain app follows a consistent shape:

- `models.py`: future model entry point
- `services/`: business operations
- `selectors/`: read/query helpers
- `api/`: DRF views, serializers, and routing
- `admin/`: Django admin integration
- `tests/`: module-local tests
- `README.md`: module responsibility and boundaries

The structure is intentionally repetitive. The goal is to make boundaries visible early so later phases do not turn into ad hoc cross-module coupling.

## Local Commands

```bash
python -m pip install -e .[dev]
python manage.py migrate
python manage.py runserver
pytest
ruff check .
black --check .
```

