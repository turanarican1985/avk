# AVK

AVK is a production-oriented Turkish legal discovery and institution platform. The platform serves visitors who want to discover legal institutions and institutions that want to manage their visibility, verification, content, and commercial access from a shared product surface.

This repository currently contains a Phase 0 bootstrap only. The goal of this phase is to establish a modular monolith foundation, documentation baseline, code quality tooling, and explicit architectural boundaries before business workflows are introduced.

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

The repository is intentionally limited to Phase 0:

- modular backend project scaffold
- health and service-info API surface
- audit and permission abstractions
- frontend placeholders
- engineering documentation
- linting, formatting, and test tooling
- automatic local `.env` loading and Phase 0 smoke tests

Out of scope for this phase:

- real domain workflows
- final institution, review, billing, or moderation models
- payment provider integration
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
