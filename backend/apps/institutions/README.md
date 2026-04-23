# Institutions

The `institutions` app owns the shared institution entity and the relationship between institutions and users. It supports both solo and team-based institutions through one model with `institution_type`, rather than splitting the product into separate top-level business systems.

Phase 1 includes:

- the core `Institution` model
- institution memberships for owners, managers, and editors
- service functions for creation and membership attachment
- selectors for common institution reads
