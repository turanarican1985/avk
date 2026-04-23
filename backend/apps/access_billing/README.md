# Access Billing

The `access_billing` app owns the commercial-access foundation for AVK.

Phase 2 includes:

- access plans for 1, 3, 6, and 12 month paid periods
- percentage-based coupons with explicit applicability rules
- a dedicated institution commercial-access state family
- payment-method references that avoid raw card storage
- scheduled future charge records
- charge attempt history and recovery-oriented state transitions

This module is intentionally separate from institution verification. Legal approval may make an institution eligible to start access, but it does not create paid access automatically.

Commercial-access transitions are intentionally guarded in the service layer:

- access start only works from a valid pre-start commercial state
- reminders only apply while a charge schedule is still in pre-charge states
- scheduled charging state is separate from individual charge-attempt outcome state
- final charge outcomes are one-way and cannot be re-finalized on the same schedule

This keeps the boundary explicit for later phases without introducing provider integration, retry orchestration, or entitlement enforcement yet.
