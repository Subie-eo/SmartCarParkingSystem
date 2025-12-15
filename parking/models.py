"""
parking.models
----------------
Core data models for the CarParking application:
- ParkingSlot: represents an individual parking space
- Booking: records user reservations and payment state

This module contains lightweight domain logic (fee calculation and slot occupation
updates) so that views and payment callbacks can rely on model behaviour.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class ParkingSlot(models.Model):
    PRICE_CHOICES = (
        ("Regular", "Regular"),
        ("Premium", "Premium"),
        ("VIP", "VIP"),
    )

    slot_id = models.CharField(max_length=10, unique=True)
    slot_name = models.CharField(max_length=50)
    level = models.CharField(max_length=20)
    pricing_category = models.CharField(max_length=20, choices=PRICE_CHOICES, default="Regular")
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.slot_name} ({self.slot_id})"

    class Meta:
        ordering = ["slot_id"]


class Booking(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_PAID = "PAID"
    STATUS_FAILED = "FAILED"

    PAYMENT_STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(blank=True, null=True)
    total_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default=STATUS_PENDING)
    mpesa_receipt_no = models.CharField(max_length=50, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id} - {self.user.email} ({self.payment_status})"

    def calculate_fee(self):
        if not self.end_time:
            return 0
        duration = self.end_time - self.start_time
        hours = duration.total_seconds() / 3600
        # Use PricingRate if available so admins can adjust prices without code changes
        try:
            rate = PricingRate.get_rate_for_category(self.slot.pricing_category)
        except Exception:
            rate = 50 if self.slot.pricing_category == "Regular" else 100 if self.slot.pricing_category == "Premium" else 150
        return round(hours * rate, 2)

    def save(self, *args, **kwargs):
        # If the booking has an end_time, compute the total fee before persisting
        if self.end_time:
            self.total_fee = self.calculate_fee()

        # Persist booking first so we have an ID for payment tracking
        super().save(*args, **kwargs)

        # Post-save side-effect: when a booking is marked PAID we make the
        # associated slot occupied. We intentionally do NOT mark the slot
        # occupied for PENDING or FAILED payments to avoid accidental holds.
        if self.payment_status == self.STATUS_PAID:
            self.slot.is_occupied = True
            self.slot.save()


class Subscription(models.Model):
    """Stores newsletter/subscription emails from the homepage."""
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=50, blank=True, default='homepage')

    def __str__(self):
        return f"Subscription {self.email}"


class PricingRate(models.Model):
    """Global pricing per category. Administrators can update these rates.
    This allows dynamic pricing without changing code.
    """
    CATEGORY_CHOICES = ParkingSlot.PRICE_CHOICES

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)
    rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('50.00'))

    class Meta:
        ordering = ['category']

    def __str__(self):
        return f"{self.category} - KES {self.rate}"

    @classmethod
    def get_rate_for_category(cls, category):
        try:
            pr = cls.objects.get(category=category)
            return float(pr.rate)
        except Exception:
            # Fallback to legacy hardcoded mapping
            return 50.0 if category == 'Regular' else 100.0 if category == 'Premium' else 150.0
