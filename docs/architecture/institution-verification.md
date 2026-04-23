# Institution Verification

This document explains the Phase 1 verification foundation in AVK.

## Why Verification Is Its Own Domain

Institution verification answers one narrow question: has the platform accepted the institution's legal and institutional proof?

It does not answer:

- whether the institution has started the 1-month full-feature access period
- whether a card has been captured
- whether a charge is scheduled
- whether premium visibility is active

That separation is essential because legal approval and commercial access are different operational concerns.

## Core Records

Phase 1 introduces four main verification records:

- `InstitutionVerificationCase`
- `InstitutionVerificationDocument`
- `InstitutionAIScreeningResult`
- `InstitutionVerificationDecision`

Together they allow the system to represent submitted evidence, AI routing output, human decisions, and support-linked re-upload behavior without collapsing those concerns together.

## AI Routing

AI is modeled as a pre-screening step with explicit outcomes:

- clean
- flagged for human review
- rejected at very high confidence

The important rule is that AI does not grant final approval. A clean AI result still routes to human review. Only very high-confidence cases may be directly rejected at the AI layer.

Phase 1 fix-up rules also make this operationally strict:

- AI routing only runs after a normal institution-portal submission
- AI routing is blocked once a submission is marked as AI-bypassed
- AI never moves a case into `approved`

## Human Decisions

Human reviewers record explicit decisions:

- approved
- rejected
- correction requested

Those decisions are stored separately from AI results so the history remains inspectable and future audit requirements stay manageable.

Human decisions are intentionally guarded by case state. In the current Phase 1 implementation they are only valid while the case is in `human_review_pending`. This prevents accidental finalization from draft, raw submitted, or already terminal states.

## Support-Linked Re-upload

Support-linked re-upload exists for correction or polite rejection paths. In Phase 1 the support system itself is not built yet, but the verification domain already models the important rule:

- re-upload documents are marked with `support_reupload`
- the current submission is marked as AI-bypassed
- the case routes directly to human review

This keeps the future workflow unambiguous without prematurely building support tickets or queueing logic.

The service layer now enforces this explicitly:

- support-linked re-upload is only allowed when the case explicitly enables it
- the re-upload moves directly to `human_review_pending`
- AI routing on that submission is blocked afterward
