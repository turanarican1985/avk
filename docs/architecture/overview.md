# Architecture Overview

## What AVK Is

AVK is a Turkish legal discovery and institution platform. It brings two audiences into one product system:

- visitors who discover institutions, read profiles, read legal content, and submit verified reviews
- institutions that manage verification, visibility, content, website presence, and commercial access

The repository is intentionally organized as a modular monolith. Phase 0 established the boundaries and operational scaffolding. Phase 1 adds the first real domain layer for accounts, institutions, and institution verification while keeping billing, websites, content, reviews, and support workflows out of scope.

## Why a Custom User Model Was Introduced Early

AVK needs stable user references for several future relationships:

- institution ownership
- institution operators and editors
- staff users
- moderators
- admins

Introducing a custom user model in Phase 1 prevents a much riskier migration later. The early model is intentionally small, email-based, and Django-compatible so the project can keep moving without locking itself into the default auth model.

## Why Institution Is the Main Entity

The top-level business entity is `institution`. This is a deliberate product choice. Solo lawyers and team-based organizations should not become separate business systems because the platform, billing, verification, content, and reputation layers overlap heavily.

Instead, the system should model a shared institution core with a type distinction such as:

- `institution_type = solo`
- `institution_type = team_based`

That choice protects the codebase from duplicated onboarding, duplicated billing logic, duplicated moderation paths, and divergent public discovery behavior.

Phase 1 turns that rule into code by introducing one `Institution` model plus institution memberships for owners, managers, and editors.

## Why State Families Must Stay Separate

AVK has several stateful concerns, but they do not mean the same thing and should not be represented by one overloaded status field.

Examples:

- a legally approved institution may not have started its commercial access period yet
- a paid plan may be scheduled while legal verification is already complete
- content moderation decisions do not determine support case status
- review verification does not imply review publication
- an institution website may degrade gracefully for billing reasons while the public institution profile remains visible

Keeping these concerns separate reduces accidental coupling and makes operational reasoning clearer for both developers and staff teams.

Phase 1 applies this rule concretely by giving institution verification its own models, services, and state transitions. Verification cases do not contain subscription, charging, coupon, or access-period fields.

## Why AI Routing Is Not Human Approval

AI is used as a routing layer, not as the final source of institutional truth.

- AI may identify a very high-confidence rejection scenario
- AI may flag a case for human attention
- AI may find no obvious high-confidence issue

In all non-obvious cases, the case still routes to human review. A clean AI result does not mean the institution is approved. Human verification decisions remain explicit and auditable.

## Why Support-Linked Re-upload Bypasses AI

Support-linked re-upload exists to handle correction and re-submission paths without sending the same case through automated screening again. In Phase 1 this is modeled inside the verification domain itself:

- the re-upload source is explicitly tracked
- the case records that the current submission bypassed AI
- the case routes directly back to human review

This keeps the rule visible without prematurely building the full support system.

## Why a Modular Monolith

AVK is early enough that a modular monolith is the most responsible default:

- shared transactions and shared data remain straightforward
- product iteration is faster than coordinating multiple services
- module boundaries can be made explicit before the system is large
- later service extraction can happen from real pressure, not assumption

The goal is not to keep everything in one app. The goal is to keep one deployable system with strong boundaries, explicit module ownership, and clear interfaces across domains.
