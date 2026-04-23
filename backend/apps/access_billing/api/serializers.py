"""Internal serializers for the commercial-access scaffolding API."""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.access_billing.models import (
    AccessPlan,
    ChargeSchedule,
    InstitutionAccessState,
)
from apps.access_billing.selectors import get_coupon_by_code
from apps.access_billing.services import start_full_feature_access_period


class AccessPlanSerializer(serializers.ModelSerializer):
    """Representation of an active access plan."""

    class Meta:
        model = AccessPlan
        fields = [
            "id",
            "code",
            "name",
            "duration_months",
            "base_price_amount",
            "currency",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ChargeScheduleSerializer(serializers.ModelSerializer):
    """Representation of a scheduled future charge."""

    coupon_code = serializers.CharField(source="coupon.code", read_only=True)
    plan_code = serializers.CharField(source="plan.code", read_only=True)

    class Meta:
        model = ChargeSchedule
        fields = [
            "id",
            "plan",
            "plan_code",
            "coupon",
            "coupon_code",
            "original_amount",
            "discounted_amount",
            "currency",
            "scheduled_for",
            "status",
            "seven_day_reminder_due_at",
            "seven_day_reminder_marked_at",
            "three_day_reminder_due_at",
            "three_day_reminder_marked_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InstitutionAccessStateSerializer(serializers.ModelSerializer):
    """Representation of the institution commercial-access state."""

    selected_plan_code = serializers.CharField(
        source="selected_plan.code",
        read_only=True,
    )
    payment_method_masked_display = serializers.CharField(
        source="active_payment_method.masked_display",
        read_only=True,
    )
    current_charge_schedule = serializers.SerializerMethodField()

    class Meta:
        model = InstitutionAccessState
        fields = [
            "id",
            "institution",
            "current_state",
            "access_period_started_at",
            "access_period_ends_at",
            "selected_plan",
            "selected_plan_code",
            "active_payment_method",
            "payment_method_masked_display",
            "scheduled_first_charge_at",
            "last_charge_success_at",
            "last_charge_failure_at",
            "recovery_started_at",
            "current_charge_schedule",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_current_charge_schedule(self, obj):
        current_schedule = obj.charge_schedules.order_by(
            "-scheduled_for",
            "-created_at",
        ).first()
        if current_schedule is None:
            return None
        return ChargeScheduleSerializer(current_schedule, context=self.context).data


class PaymentMethodReferenceInputSerializer(serializers.Serializer):
    """Safe payment-method metadata expected during access start."""

    provider_name = serializers.CharField(max_length=64)
    provider_customer_reference = serializers.CharField(max_length=255)
    provider_payment_method_reference = serializers.CharField(max_length=255)
    masked_display = serializers.CharField(max_length=64)
    card_brand = serializers.CharField(max_length=64, required=False, allow_blank=True)
    expiry_month = serializers.IntegerField(required=False, min_value=1, max_value=12)
    expiry_year = serializers.IntegerField(required=False, min_value=2000)


class StartInstitutionAccessSerializer(serializers.Serializer):
    """Minimal payload for starting the full-feature access period."""

    plan_id = serializers.UUIDField()
    coupon_code = serializers.CharField(
        max_length=64,
        required=False,
        allow_blank=True,
    )
    payment_method = PaymentMethodReferenceInputSerializer()

    def create(self, validated_data):
        request = self.context["request"]
        institution = self.context["institution"]
        try:
            plan = AccessPlan.objects.get(id=validated_data["plan_id"], is_active=True)
        except ObjectDoesNotExist as exc:
            raise serializers.ValidationError(
                {"plan_id": "Active access plan could not be found."}
            ) from exc
        coupon = None
        coupon_code = validated_data.get("coupon_code")
        if coupon_code:
            try:
                coupon = get_coupon_by_code(code=coupon_code)
            except ObjectDoesNotExist as exc:
                raise serializers.ValidationError(
                    {"coupon_code": "Coupon could not be found."}
                ) from exc
        return start_full_feature_access_period(
            institution=institution,
            plan=plan,
            payment_method_payload=validated_data["payment_method"],
            coupon=coupon,
            actor_id=str(request.user.id),
        )

    def to_representation(self, instance):
        return InstitutionAccessStateSerializer(instance, context=self.context).data
