#!/usr/bin/env python3
"""Debug helper: list bookings for a username or email.
Run: python scripts/debug_bookings.py --username sub
"""
import os
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--username', help='username to inspect')
parser.add_argument('--email', help='email to inspect')
args = parser.parse_args()

# Ensure project root is on sys.path when running from scripts/ directory
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
# Now set the settings module and initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CarParking.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from parking.models import Booking, ParkingSlot
from django.utils import timezone

User = get_user_model()
user = None
if args.username:
    try:
        user = User.objects.get(username=args.username)
    except User.DoesNotExist:
        print(f"No user with username={args.username}")
        sys.exit(2)
elif args.email:
    try:
        user = User.objects.get(email=args.email)
    except User.DoesNotExist:
        print(f"No user with email={args.email}")
        sys.exit(2)
else:
    print("Provide --username or --email")
    sys.exit(2)

now = timezone.now()
print(f"User: {user} (id={user.id})\nNow: {now.isoformat()}")

qs = Booking.objects.filter(user=user).order_by('-created_at')
print(f"Total bookings: {qs.count()}\n")
for b in qs:
    print(f"Booking #{b.id}: slot={getattr(b.slot, 'slot_id', None)} status={b.payment_status} created={b.created_at} start={b.start_time} end={b.end_time}")

# Show any occupied slots linked to this user
occ = ParkingSlot.objects.filter(is_occupied=True, booking__user=user).distinct()
print('\nOccupied slots linked to user:')
for s in occ:
    print(f" - {s.slot_id} (is_occupied={s.is_occupied})")

# Show recent pending that would block (last 15 minutes)
from django.utils import timezone
window = now - timezone.timedelta(minutes=15)
recent_pending = Booking.objects.filter(user=user, payment_status=Booking.STATUS_PENDING, created_at__gte=window)
print(f"\nRecent pending bookings (last 15 minutes): {recent_pending.count()}")
for b in recent_pending:
    print(f" - #{b.id} created={b.created_at} slot={b.slot.slot_id} start={b.start_time} end={b.end_time}")

# Show active paid bookings (start<=now<end and slot occupied)
active_paid = Booking.objects.filter(user=user, payment_status=Booking.STATUS_PAID, start_time__lte=now, end_time__gt=now, slot__is_occupied=True)
print(f"\nActive paid bookings that block booking: {active_paid.count()}")
for b in active_paid:
    print(f" - #{b.id} slot={b.slot.slot_id} start={b.start_time} end={b.end_time} slot.is_occupied={b.slot.is_occupied}")
