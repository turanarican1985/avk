# Architecture Overview

## What AVK Is

AVK is a Turkish legal discovery and institution platform. It brings two audiences into one product system:

- visitors who discover institutions, read profiles, read legal content, and submit verified reviews
- institutions that manage verification, visibility, content, website presence, and commercial access

The repository is intentionally organized as a modular monolith. Phase 0 establishes the boundaries and operational scaffolding so later phases can add workflows without collapsing the design into a tangle of cross-cutting conditionals.

## Why Institution Is the Main Entity

The top-level business entity is `institution`. This is a deliberate product choice. Solo lawyers and team-based organizations should not become separate business systems because the platform, billing, verification, content, and reputation layers overlap heavily.

Instead, the system should model a shared institution core with a type distinction such as:

- `institution_type = solo`
- `institution_type = team_based`

That choice protects the codebase from duplicated onboarding, duplicated billing logic, duplicated moderation paths, and divergent public discovery behavior.

## Why State Families Must Stay Separate

AVK has several stateful concerns, but they do not mean the same thing and should not be represented by one overloaded status field.

Examples:

- a legally approved institution may not have started its commercial access period yet
- a paid plan may be scheduled while legal verification is already complete
- content moderation decisions do not determine support case status
- review verification does not imply review publication
- an institution website may degrade gracefully for billing reasons while the public institution profile remains visible

Keeping these concerns separate reduces accidental coupling and makes operational reasoning clearer for both developers and staff teams.

## Why a Modular Monolith

AVK is early enough that a modular monolith is the most responsible default:

- shared transactions and shared data remain straightforward
- product iteration is faster than coordinating multiple services
- module boundaries can be made explicit before the system is large
- later service extraction can happen from real pressure, not assumption

The goal is not to keep everything in one app. The goal is to keep one deployable system with strong boundaries, explicit module ownership, and clear interfaces across domains.

