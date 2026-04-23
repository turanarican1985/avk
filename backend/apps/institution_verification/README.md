# Institution Verification

The `institution_verification` app owns legal and institutional proof intake, AI routing outcomes, human verification decisions, and the support-linked re-upload boundary.

Phase 1 includes:

- explicit verification case state that is separate from billing and commercial access
- document records with source tracking for institution submissions and support-linked re-uploads
- AI screening results as routing signals rather than final approval
- human decision history for approval, rejection, and correction requests
- support-linked re-upload handling that bypasses AI and routes directly to human review

The service layer intentionally blocks invalid transitions. In particular:

- AI routing is only allowed after a normal institution-portal submission
- AI cannot run on support-linked re-upload submissions
- human decisions are only allowed while the case is pending human review
- support-linked re-upload is only allowed when explicitly enabled by the case state
