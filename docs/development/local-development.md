# Local Development

This document explains the intended local development flow for the AVK backend bootstrap. Some services are placeholders in Phase 0, but the workflow is realistic enough for day-to-day development.

## Backend

1. Install Python 3.12.
2. Create and activate a virtual environment.
3. Copy `backend/.env.example` to `backend/.env`.
4. Install dependencies:

   ```bash
   cd backend
   python -m pip install -e .[dev]
   ```

5. Run migrations:

   ```bash
   python manage.py migrate
   ```

6. Start the development server:

   ```bash
   python manage.py runserver
   ```

## Database Notes

PostgreSQL is the intended primary database for real environments. Phase 0 allows SQLite in local development by default so contributors can boot the repository quickly before domain models exist.

When PostgreSQL-backed development becomes necessary, set `USE_SQLITE=false` and provide the PostgreSQL environment variables from `.env`.

## Background Jobs

Celery and Redis are configured as placeholders. The bootstrap defines the configuration seam, but no real task workflows are implemented yet.

Future local workflow will look like:

```bash
celery -A config worker -l info
```

## Quality Checks

Run the Python quality tools from `backend/`:

```bash
ruff check .
black --check .
pytest
```

