"""Institution write services."""

from .institutions import (
    attach_institution_membership,
    attach_owner_membership,
    create_institution,
)

__all__ = [
    "attach_institution_membership",
    "attach_owner_membership",
    "create_institution",
]
