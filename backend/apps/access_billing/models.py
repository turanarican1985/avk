"""Commercial access and billing foundation models."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.institutions.models import Institution


class AccessPlanDurationMonths(models.IntegerChoices):
    """Supported plan periods in months."""

    ONE = 1, "1 Month"
    THREE = 3, "3 Months"
    SIX = 6, "6 Months"
    TWELVE = 12, "12 Months"


class InstitutionAccessStatus(models.TextChoices):
    """Commercial access lifecycle states."""

    NOT_STARTED = "not_started", "Not Started"
    ELIGIBLE_TO_START = "eligible_to_start", "Eligible To Start"
    ACCESS_ACTIVE = "access_active", "Access Active"
    ACCESS_EXPIRING_SOON = "access_expiring_soon", "Access Expiring Soon"
    AWAITING_FIRST_CHARGE = "awaiting_first_charge", "Awaiting First Charge"
    PAID_ACTIVE = "paid_active", "Paid Active"
    PAYMENT_DUE = "payment_due", "Payment Due"
    PAYMENT_FAILED = "payment_failed", "Payment Failed"
    RECOVERY_ACTIVE = "recovery_active", "Recovery Active"
    PAUSED_OR_RESTRICTED = "paused_or_restricted", "Paused Or Restricted"


class ChargeScheduleStatus(models.TextChoices):
    """States for scheduled charge execution."""

    PENDING = "pending", "Pending"
    READY = "ready", "Ready"
    CHARGE_IN_PROGRESS = "charge_in_progress", "Charge In Progress"
    CHARGE_SUCCEEDED = "charge_succeeded", "Charge Succeeded"
    CHARGE_FAILED = "charge_failed", "Charge Failed"
    CANCELLED = "cancelled", "Cancelled"


class ChargeAttemptOutcome(models.TextChoices):
    """Outcomes for individual charge attempts."""

    PENDING = "pending", "Pending"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"


class AccessPlan(models.Model):
    """Selectable commercial plan for a future scheduled charge."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    duration_months = models.PositiveSmallIntegerField(
        choices=AccessPlanDurationMonths.choices
    )
    base_price_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    currency = models.CharField(max_length=3, default="TRY")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["duration_months", "base_price_amount", "code"]

    def __str__(self) -> str:
        return f"{self.name} ({self.duration_months}m)"


class Coupon(models.Model):
    """Percentage-based coupon definition."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(Decimal("99.99")),
        ],
    )
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    applies_to_all_plans = models.BooleanField(default=False)
    applicable_plans = models.ManyToManyField(
        AccessPlan,
        blank=True,
        related_name="coupons",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def clean(self) -> None:
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_from > self.valid_until
        ):
            raise ValidationError("Coupon valid_from must be earlier than valid_until.")

    def __str__(self) -> str:
        return self.code


class PaymentMethodReference(models.Model):
    """Captured payment method metadata without sensitive card data."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="payment_method_references",
    )
    provider_name = models.CharField(max_length=64)
    provider_customer_reference = models.CharField(max_length=255)
    provider_payment_method_reference = models.CharField(max_length=255)
    masked_display = models.CharField(max_length=64)
    card_brand = models.CharField(max_length=64, blank=True)
    expiry_month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    expiry_year = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.provider_name} - {self.masked_display}"


class InstitutionAccessState(models.Model):
    """Commercial-access state for an institution."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    institution = models.OneToOneField(
        Institution,
        on_delete=models.CASCADE,
        related_name="access_state",
    )
    current_state = models.CharField(
        max_length=32,
        choices=InstitutionAccessStatus.choices,
        default=InstitutionAccessStatus.NOT_STARTED,
    )
    access_period_started_at = models.DateTimeField(null=True, blank=True)
    access_period_ends_at = models.DateTimeField(null=True, blank=True)
    selected_plan = models.ForeignKey(
        AccessPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="institution_access_states",
    )
    active_payment_method = models.ForeignKey(
        PaymentMethodReference,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_for_access_states",
    )
    scheduled_first_charge_at = models.DateTimeField(null=True, blank=True)
    last_charge_success_at = models.DateTimeField(null=True, blank=True)
    last_charge_failure_at = models.DateTimeField(null=True, blank=True)
    recovery_started_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["institution__display_name"]

    def __str__(self) -> str:
        return f"{self.institution} - {self.current_state}"


class ChargeSchedule(models.Model):
    """Scheduled future charge for an institution's commercial access."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    access_state = models.ForeignKey(
        InstitutionAccessState,
        on_delete=models.CASCADE,
        related_name="charge_schedules",
    )
    plan = models.ForeignKey(
        AccessPlan,
        on_delete=models.PROTECT,
        related_name="charge_schedules",
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="charge_schedules",
    )
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    scheduled_for = models.DateTimeField()
    status = models.CharField(
        max_length=32,
        choices=ChargeScheduleStatus.choices,
        default=ChargeScheduleStatus.PENDING,
    )
    seven_day_reminder_due_at = models.DateTimeField(null=True, blank=True)
    seven_day_reminder_marked_at = models.DateTimeField(null=True, blank=True)
    three_day_reminder_due_at = models.DateTimeField(null=True, blank=True)
    three_day_reminder_marked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_for", "created_at"]

    def __str__(self) -> str:
        return (
            f"{self.access_state.institution} - {self.plan.code} "
            f"@ {self.scheduled_for}"
        )


class ChargeAttempt(models.Model):
    """Outcome record for a charge collection attempt."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    charge_schedule = models.ForeignKey(
        ChargeSchedule,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    provider_name = models.CharField(max_length=64, blank=True)
    provider_attempt_reference = models.CharField(max_length=255, blank=True)
    attempted_at = models.DateTimeField()
    outcome = models.CharField(
        max_length=16,
        choices=ChargeAttemptOutcome.choices,
        default=ChargeAttemptOutcome.PENDING,
    )
    failure_code = models.CharField(max_length=128, blank=True)
    failure_reason = models.TextField(blank=True)
    captured_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-attempted_at", "-created_at"]

    def __str__(self) -> str:
        return f"{self.charge_schedule_id} - {self.outcome}"
