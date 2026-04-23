# Planned Modules

This document describes the intended responsibility of each backend module in the AVK modular monolith. The point is to keep business language, persistence, APIs, and operations aligned around clear ownership.

## `common`

Cross-cutting utilities that are truly shared and small in scope. This module should stay disciplined and should not become a miscellaneous catch-all.

## `audit_core`

Audit event recording, audit-read concerns, and explicit sensitive-data access logging boundaries. This module protects traceability and compliance-related visibility across the platform.

## `accounts`

Custom user model and future account-level behavior. This module exists early because institution ownership, operators, staff users, moderators, and admins all need a stable user reference.

## `institutions`

Core institution concepts. In Phase 1 this module now owns:

- the shared `Institution` entity
- institution type (`solo` or `team_based`)
- institution lifecycle status
- institution memberships for owner, manager, and editor roles

## `institution_verification`

Legal and institutional verification intake, evidence handling boundaries, AI pre-screening orchestration hooks, human verification workflow concepts, and correction/re-upload entry points.

In Phase 1 this module now owns:

- verification cases
- verification documents
- AI screening results
- human decision history
- support-linked re-upload routing that bypasses AI

## `access_billing`

Commercial access concepts such as the 1-month full-feature access period, card capture timing, scheduled charging, plan periods, coupon application rules, billing recovery coordination, and subscription visibility state.

In Phase 2 this module now owns:

- access plans for 1, 3, 6, and 12 month periods
- percentage-based coupons with explicit plan applicability
- institution commercial-access state
- payment-method references without raw card storage
- scheduled future charges and reminder boundaries
- charge attempt history and recovery-oriented transitions

## `institution_websites`

Institution-controlled website configuration, template selection, section configuration, theming, slug publishing, graceful downgrade behavior, and later custom-domain support.

## `content`

Institution-authored content such as blog entries, service descriptions, and institutional/promotional content. This module should focus on content ownership, drafting, and visibility configuration.

## `content_moderation`

Moderation state, AI review outcomes, internal post-AI approval queues, appeals, and moderation decision history for institution-authored content. It is separate from support because moderation is not a support lifecycle.

## `reviews`

Verified review submission, evidence handling boundaries, reviewer verification state, publication timing, objection windows, and dispute entry points. Reviewer contact data constraints must remain explicit here and in staff permission policy.

## `support`

Unified support intake, queue routing, case lifecycle, escalation policy, and public versus internal support surfaces. This module should not absorb moderation or verification state itself.

## `staff_ops`

Employee, moderator, team assignment, queue-level permissions, action-level permissions, override policy, and operational access boundaries. The module should support scoped moderation rather than a universal unrestricted moderator role.

## `notifications`

Cross-channel outbound communication such as email, SMS, and later notification preferences or delivery audit hooks.
