# Commercial Access

This document explains the Phase 2 commercial-access foundation in AVK.

## Why Commercial Access Is Separate From Verification

Legal verification answers whether the institution passed institutional review. Commercial access answers whether the institution has explicitly started the 1-month full-feature access period and what happens around plan selection, payment-method capture, scheduled charging, and recovery.

These are different operational concerns:

- legal approval does not automatically start access
- selected plan does not mean successful payment
- captured payment method does not mean charged payment
- scheduled charge does not mean successful subscription activation

## Access Start

Phase 2 models the rule that access begins only after legal approval and explicit institution action.

At access start:

- the institution chooses a plan
- a safe payment-method reference is captured
- the 1-month full-feature access period begins
- the first future charge is scheduled for the end of that period

## Plans

Phase 2 access plans are intentionally narrow and production-oriented:

- 1 month
- 3 months
- 6 months
- 12 months

Each plan carries a base price and currency but does not yet model marketing-page presentation or admin pricing UI.

## Coupons

Coupons are percentage-based only. They:

- must be greater than 0 and less than 100
- may be active or inactive
- may be time-bounded
- may be limited by usage count
- may apply to all plans or to specific plans explicitly

## Payment Method Reference

The system stores payment-method references, not raw card data.

This means the model may hold:

- provider name
- provider customer reference
- provider payment-method reference
- masked display info
- card brand and expiry metadata

It must not hold raw card number or PCI-sensitive card data.

## Charge Schedule Versus Charge Attempt

Scheduled charging is modeled separately from actual charge attempts.

`ChargeSchedule` answers:

- what amount is expected
- when charging is scheduled
- whether reminder boundaries exist
- whether the schedule is pending, ready, succeeded, failed, or cancelled

`ChargeAttempt` answers:

- when an actual attempt happened
- whether it succeeded or failed
- what failure reference was recorded
- what amount was captured if any

That separation keeps planning state and execution state distinct.

## Recovery Foundation

Phase 2 does not implement full retry orchestration or provider integration, but it does introduce failure and recovery-oriented state transitions so later phases can build on clean domain boundaries.
