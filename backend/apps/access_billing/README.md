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
