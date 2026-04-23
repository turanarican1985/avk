"""Admin integration for access and billing models."""

from django.contrib import admin

from apps.access_billing.models import (
    AccessPlan,
    ChargeAttempt,
    ChargeSchedule,
    Coupon,
    InstitutionAccessState,
    PaymentMethodReference,
)


@admin.register(AccessPlan)
class AccessPlanAdmin(admin.ModelAdmin):
    """Admin configuration for access plans."""

    list_display = (
        "code",
        "name",
        "duration_months",
        "base_price_amount",
        "currency",
        "is_active",
    )
    list_filter = ("duration_months", "currency", "is_active")
    search_fields = ("code", "name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Admin configuration for coupons."""

    list_display = (
        "code",
        "discount_percent",
        "is_active",
        "applies_to_all_plans",
        "valid_from",
        "valid_until",
        "usage_limit",
        "usage_count",
    )
    list_filter = ("is_active", "applies_to_all_plans")
    search_fields = ("code",)
    readonly_fields = ("id", "usage_count", "created_at", "updated_at")
    filter_horizontal = ("applicable_plans",)


@admin.register(PaymentMethodReference)
class PaymentMethodReferenceAdmin(admin.ModelAdmin):
    """Admin configuration for payment method references."""

    list_display = (
        "institution",
        "provider_name",
        "masked_display",
        "card_brand",
        "is_active",
        "created_at",
    )
    list_filter = ("provider_name", "card_brand", "is_active")
    search_fields = (
        "institution__display_name",
        "provider_customer_reference",
        "provider_payment_method_reference",
        "masked_display",
    )
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(InstitutionAccessState)
class InstitutionAccessStateAdmin(admin.ModelAdmin):
    """Admin configuration for institution commercial-access state."""

    list_display = (
        "institution",
        "current_state",
        "selected_plan",
        "scheduled_first_charge_at",
        "access_period_started_at",
        "access_period_ends_at",
    )
    list_filter = ("current_state",)
    search_fields = (
        "institution__display_name",
        "institution__legal_name",
        "institution__slug",
    )
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ChargeSchedule)
class ChargeScheduleAdmin(admin.ModelAdmin):
    """Admin configuration for charge schedules."""

    list_display = (
        "access_state",
        "plan",
        "status",
        "discounted_amount",
        "currency",
        "scheduled_for",
    )
    list_filter = ("status", "currency")
    search_fields = (
        "access_state__institution__display_name",
        "plan__code",
        "coupon__code",
    )
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ChargeAttempt)
class ChargeAttemptAdmin(admin.ModelAdmin):
    """Admin configuration for charge attempts."""

    list_display = (
        "charge_schedule",
        "outcome",
        "captured_amount",
        "attempted_at",
        "provider_name",
    )
    list_filter = ("outcome", "provider_name")
    search_fields = (
        "charge_schedule__access_state__institution__display_name",
        "provider_attempt_reference",
        "failure_code",
    )
    readonly_fields = ("id", "created_at", "updated_at")
