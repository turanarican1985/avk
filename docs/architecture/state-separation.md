# State Separation

State separation is one of the most important architectural rules in AVK. Different operational questions require different state families. Collapsing them into one shared status field would make the system hard to reason about and easy to break.

## Institution Legal Verification

This state family answers whether the institution's legal identity and submitted proof have passed the verification process. It does not answer anything about pricing, card capture, or paid access.

Phase 1 models this explicitly through institution verification cases, AI screening results, and human verification decisions. AI routing and human approval remain distinct concerns even inside the verification domain.

## 1-Month Full-Feature Access and Commercial Access

This state family answers whether a legally approved institution has started the 1-month full-feature access period, whether a paid period is active, and whether premium entitlements are currently available.

## Card Capture and Charge Scheduling

This state family answers whether payment details were captured, which plan period was selected, whether a charge is scheduled, and what reminder milestones exist before charging.

## Content Moderation

This state family answers where institution-authored content sits in the moderation process. It is independent from support tickets and independent from institution legal verification.

## Review Verification and Publication

This area needs at least two conceptual tracks:

- review verification state
- review publication state

A review can be verified and still remain unpublished during an objection window or dispute process.

## Support Case Lifecycle

Support cases need their own lifecycle because support is an operational handling process. A support case may reference verification, billing, content, or review topics without becoming the source of truth for those state families.

Phase 1 only introduces the support-linked re-upload boundary inside the verification domain. It does not introduce the full support lifecycle, support queues, or support ticket models.

## Institution Website Lifecycle

Institution website state must remain separate from both the core institution profile and the billing lifecycle. Billing problems may require graceful website degradation, but the institution profile should not disappear solely because billing is unresolved.

## AI Routing Versus Human Decisions

AI routing state answers whether a submission looks clean, suspicious, or obviously problematic at very high confidence. Human decision state answers whether a reviewer approved, rejected, or requested correction.

Those questions must not be collapsed together:

- AI clean does not equal approved
- AI rejection is only for very high-confidence cases
- support-linked re-upload bypasses AI and returns to human review
- human decisions are intentionally blocked unless the case is in a valid reviewable state
