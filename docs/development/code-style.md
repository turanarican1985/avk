# Code Style

## Language Rules

- User-facing product copy must be Turkish.
- Internal code, comments, docstrings, commit-oriented documentation, and engineering markdown should be English.
- Internal English names should not leak into UI labels, dashboard copy, or public-facing product surfaces.

## Service and API Boundaries

- Keep business logic out of views.
- Put write-oriented use cases in small service functions or service objects.
- Put read/query logic in selectors so query behavior stays testable and composable.
- Keep serializers, views, and API routing thin.

## Naming and Structure

- Prefer explicit names over abbreviated ones.
- Keep modules narrow and aligned to the product language of the domain.
- Avoid catch-all utility modules unless the logic is genuinely cross-cutting.
- Preserve module boundaries even when a shortcut seems convenient.

## Testability

- Structure code so service logic can be tested without going through the entire HTTP stack.
- Keep side effects behind small seams where possible.
- Add smoke tests for minimal surfaces and focused tests for domain services as they appear.

## Auditability

- Critical transitions should emit explicit audit events.
- Access to sensitive data should be explicitly logged.
- Avoid hidden side effects in model methods when a service can make the transition clearer.

