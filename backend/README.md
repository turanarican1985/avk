# Backend Bootstrap

This directory contains the Django backend for AVK. The backend is structured as a modular monolith so that product domains can evolve independently without introducing premature service boundaries.

## What Exists Through Phase 1

- Django project configuration with environment-based settings
- Django REST Framework baseline configuration
- PostgreSQL, Celery, and Redis placeholders
- modular app packages under `apps/`
- minimal health and service-info API endpoints
- audit, permission, and sensitive-access abstractions
- automatic `.env` loading for local development
- custom email-based user model
- institution and institution membership domain models
- institution verification models, services, selectors, admin, and migrations
- thin internal scaffolding APIs for institution and verification case inspection
- pytest, Ruff, and Black configuration

## What Does Not Exist Yet

- payment provider integrations
- billing and commercial access workflows
- institution website builder logic
- content and moderation workflows
- verified review workflows
- full support system implementation
- production staff permission matrix

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

## Phase 1 Notes

- `accounts` introduces the project's custom user model early to avoid a risky late auth migration.
- `institutions` models the shared institution entity for both solo and team-based organizations.
- `institution_verification` keeps verification state separate from commercial access and uses AI only for routing, not final approval.
- support-linked re-upload is modeled as a verification-domain boundary that bypasses AI and routes directly to human review.

## Local Commands

```bash
python -m pip install -e .[dev]
python manage.py migrate
python manage.py runserver
pytest
ruff check .
black --check .
```

Copy `.env.example` to `.env` before running local commands. The settings package loads that file automatically so contributors do not need to export variables manually during Phase 0.
