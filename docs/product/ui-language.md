# UI Language Rules

AVK is a Turkish product. All user-facing interface text should be Turkish unless there is a legally required exception.

## Required Direction

- public pages use Turkish copy
- dashboards use Turkish copy
- institution-facing marketing pages use Turkish copy
- operational labels shown to institutions or visitors use Turkish copy

## Internal Naming

Engineering names may remain English where that improves maintainability:

- module names
- Python identifiers
- API internals
- comments and docstrings
- engineering documentation

## Boundary Rule

Internal English names such as `trial_access`, `institution_website`, or `institution_verification` should not be exposed directly in product surfaces. Product-facing terminology must use the approved Turkish wording for the platform experience.

