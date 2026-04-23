# AVK

AVK is a production-oriented Turkish legal discovery and institution platform. The platform serves visitors who want to discover legal institutions and institutions that want to manage their visibility, verification, content, and commercial access from a shared product surface.

This repository currently contains the Phase 0 foundation plus a bounded Phase 1 domain layer for accounts, institutions, and institution verification. The goal is to establish real core models and services without leaking into billing, websites, content, reviews, or the full support system too early.

## Stack Direction

- Backend: Python 3.12, Django, Django REST Framework, PostgreSQL, Celery, Redis
- Frontend public surfaces: Nuxt 3
- Frontend authenticated surfaces: Vue 3
- Styling direction: Tailwind CSS
- Architecture: modular monolith first, service extraction later only if justified

## Repository Layout

- `backend/`: Django project bootstrap, modular apps, tests, and Python tooling
- `frontend/`: placeholder structure for the future public site and institution dashboard
- `docs/`: architecture, development, and product-language documentation
- `.github/workflows/`: CI bootstrap for linting and tests

## Current Status

The repository currently includes the Phase 0 foundation and the bounded Phase 1 institution and verification domain layer:

- modular backend project scaffold
- health and service-info API surface
- audit and permission abstractions
- custom user model
- institution and institution membership domain models
- institution verification domain models and services
- frontend placeholders
- engineering documentation
- linting, formatting, and test tooling
- automatic local `.env` loading and Phase 0 smoke tests

Out of scope for the current repository state:

- payment provider integration
- billing/commercial access logic
- institution website builder behavior
- content and moderation workflows
- verified review workflows
- support chat implementation
- production permission matrix

## Architectural Rules

- `institution` is the top-level business entity for both solo and team-based organizations.
- Legal verification state, commercial access state, review verification state, content moderation state, support lifecycle state, and institution website state must remain separate.
- User-facing product copy must be Turkish. Internal code, comments, docstrings, and engineering documentation remain English.
- Business logic should live in explicit services and selectors, not inside views.
- DRF defaults should be conservative, with public endpoints opting into openness explicitly.
- Critical transitions should be designed with auditability in mind from the beginning.

## Documentation

Start with [docs/README.md](docs/README.md). The architecture documents explain the modular boundary plan, the state-separation rules, and the development workflow expected for future phases.
