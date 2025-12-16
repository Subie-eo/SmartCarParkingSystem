"""
parking.views
---------------
Views for the parking app including:
- Admin slot management and booking lists
- Driver-facing slot listing and booking initiation
- Booking status and helper endpoints used by payment callbacks

The views try to keep logic thin and reuse model behaviour where possible.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from datetime import datetime
from .models import ParkingSlot, Booking
from .models import PricingRate
from parkingpayments.mpesa import get_client
from .forms import ParkingSlotForm, BookingForm
from django.utils import timezone
from django.db.models import Q, Sum
from django.http import JsonResponse
import re

# --- Helper: Check if user is admin ---
def is_admin(user):
    return user.is_staff or user.is_superuser


def _get_slot_vehicle_types():
    """Return a dict mapping slot_id -> vehicle_type for currently occupied slots.
    This helps templates render a small icon representing the occupant's vehicle.
    """
    mapping = {}
    occupied_slots = ParkingSlot.objects.filter(is_occupied=True)
    for slot in occupied_slots:
        # find the most recent PAID booking for this slot (if any)
        booking = Booking.objects.filter(slot=slot, payment_status=Booking.STATUS_PAID).order_by('-created_at').first()
        if booking and getattr(booking.user, 'vehicle_type', None):
            mapping[slot.slot_id] = booking.user.vehicle_type
    return mapping


def _compute_svg_slots(all_slots):
    """Given a queryset/list of slots, return a list of dicts with x/y/size/metadata
    to render parking bays in the dashboard SVG.
    Simple algorithm: group by `level` and lay slots horizontally per level.
    """
    # Convert to list to iterate multiple times
    slots = list(all_slots)
    # Group by level preserving first-seen order
    groups = {}
    order = []
    for s in slots:
        lvl = s.level or 'Level'
        if lvl not in groups:
            groups[lvl] = []
            order.append(lvl)
        groups[lvl].append(s)

    svg_slots = []
    # layout parameters
    slot_w = 110
    slot_h = 58
    gap = 18
    left_margin = 260
    top_margin = 48
    level_gap = slot_h + 48

    for li, lvl in enumerate(order):
        rowslots = groups.get(lvl, [])
        y = top_margin + li * level_gap
        for idx, s in enumerate(rowslots):
            x = left_margin + idx * (slot_w + gap)
            svg_slots.append({
                'slot_id': s.slot_id,
                'level': lvl,
                'x': x,
                'y': y,
                'w': slot_w,
                'h': slot_h,
                'is_occupied': bool(s.is_occupied),
                'vehicle_type': getattr(s, 'vehicle_type', None),
                'cx': x + slot_w / 2,
                'cy': y + slot_h / 2,
            })

    return svg_slots

# --- 1. Admin: List & Create Parking Slots ---
@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def slot_list_create_view(request):
    slots = ParkingSlot.objects.all().order_by('slot_id')

    if request.method == 'POST':
        form = ParkingSlotForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"Parking Slot {form.instance.slot_id} created successfully.")
                return redirect('parking:admin_slot_list')
            except Exception:
                messages.error(request, "Error creating slot: Slot ID may already exist.")
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = ParkingSlotForm()

    return render(request, 'parking/admin_slot_list.html', {
        'slots': slots,
        'form': form,
        'header_title': 'Slot Inventory Management'
    })


@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def pricing_rates_view(request):
    """Admin view to see and update pricing rates for categories."""
    # Ensure a PricingRate exists for each category
    for cat, _ in ParkingSlot.PRICE_CHOICES:
        PricingRate.objects.get_or_create(category=cat, defaults={'rate': 50.00 if cat == 'Regular' else 100.00 if cat == 'Premium' else 150.00})

    from .forms import PricingForm

    if request.method == 'POST':
        form = PricingForm(request.POST)
        if form.is_valid():
            # Update or create rates
            PricingRate.objects.update_or_create(category='Regular', defaults={'rate': form.cleaned_data['regular_rate']})
            PricingRate.objects.update_or_create(category='Premium', defaults={'rate': form.cleaned_data['premium_rate']})
            PricingRate.objects.update_or_create(category='VIP', defaults={'rate': form.cleaned_data['vip_rate']})
            messages.success(request, 'Pricing rates updated successfully.')
            return redirect('parking:admin_slot_list')
        else:
            messages.error(request, 'Please correct the pricing form errors.')
    else:
        # Build initial data from existing rates
        data = {}
        try:
            data['regular_rate'] = PricingRate.objects.get(category='Regular').rate
        except PricingRate.DoesNotExist:
            data['regular_rate'] = 50.00
        try:
            data['premium_rate'] = PricingRate.objects.get(category='Premium').rate
        except PricingRate.DoesNotExist:
            data['premium_rate'] = 100.00
        try:
            data['vip_rate'] = PricingRate.objects.get(category='VIP').rate
        except PricingRate.DoesNotExist:
            data['vip_rate'] = 150.00

        form = PricingForm(initial=data)

    return render(request, 'parking/admin_pricing.html', {'form': form, 'header_title': 'Pricing Rates'})

# --- 2. Admin: Update / Delete Slot ---
@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def slot_update_delete_view(request, slot_id):
    slot = get_object_or_404(ParkingSlot, slot_id=slot_id)

    if request.method == 'POST':
        if 'delete' in request.POST:
            try:
                slot.delete()
                messages.success(request, f"Parking Slot {slot_id} deleted successfully.")
                return redirect('parking:admin_slot_list')
            except Exception:
                messages.error(request, f"Cannot delete slot {slot_id}: linked bookings exist.")
        else:
            form = ParkingSlotForm(request.POST, instance=slot)
            if form.is_valid():
                form.save()
                messages.success(request, f"Parking Slot {slot_id} updated successfully.")
                return redirect('parking:admin_slot_list')
            else:
                messages.error(request, "Please correct the errors in the form.")
    else:
        form = ParkingSlotForm(instance=slot)

    return render(request, 'parking/admin_slot_detail.html', {
        'form': form,
        'slot': slot,
        'header_title': f'Edit Slot: {slot_id}'
    })


# --- 2b. Admin: Toggle Slot Occupied Status (Quick action from list)
@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def toggle_slot_status(request, slot_id):
    """Quick toggle endpoint for administrators to flip a slot's occupied state.
    This is intended for fast corrections (e.g., freeing a slot after manual inspection).
    """
    slot = get_object_or_404(ParkingSlot, slot_id=slot_id)
    if request.method == 'POST':
        try:
            slot.is_occupied = not slot.is_occupied
            slot.save()
            messages.success(request, f"Slot {slot_id} status updated to {'OCCUPIED' if slot.is_occupied else 'FREE'}.")
        except Exception:
            messages.error(request, f"Failed to update status for slot {slot_id}.")
    return redirect('parking:admin_slot_list')

# --- 3. Admin: Booking List ---
@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def admin_booking_list_view(request):
    bookings = Booking.objects.all().order_by('-created_at')
    return render(request, 'parking/admin_booking_list.html', {
        'bookings': bookings,
        'header_title': 'Reservation & Revenue Tracker'
    })

# --- 4. Driver: Available Slots ---
@login_required
def available_slots_view(request):
    all_slots = ParkingSlot.objects.all().order_by('level', 'slot_id')
    available_slots = ParkingSlot.objects.filter(is_occupied=False).order_by('level', 'slot_id')
    booking_form = BookingForm()

    # Attach a transient `vehicle_type` attribute to occupied slot objects
    slot_vehicle_types = _get_slot_vehicle_types()
    for s in all_slots:
        s.vehicle_type = slot_vehicle_types.get(s.slot_id)

    # Get driver's recent bookings
    user_bookings = Booking.objects.filter(user=request.user).order_by('-start_time')[:5]

    # Get recent pending booking if any (to show cancel option)
    pending_booking = Booking.objects.filter(
        user=request.user,
        payment_status=Booking.STATUS_PENDING,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=15)
    ).first()

    # Calculate parking statistics
    total_slots = all_slots.count()
    occupied_count = ParkingSlot.objects.filter(is_occupied=True).count()
    available_count = total_slots - occupied_count
    availability_percentage = (available_count / total_slots * 100) if total_slots > 0 else 0

    # Determine occupancy status for the requesting user
    now = timezone.now()
    occupancy_status = 'FREE'
    pending_window = now - timezone.timedelta(minutes=15)
    if Booking.objects.filter(user=request.user, payment_status=Booking.STATUS_PENDING, created_at__gte=pending_window).exists():
        occupancy_status = 'PENDING'
    # Treat a user as OCCUPIED only if they have a PAID booking that is currently in effect
    # (start_time <= now < end_time) and the slot is still marked occupied. This avoids
    # future or past paid bookings blocking new bookings.
    elif Booking.objects.filter(
        user=request.user,
        payment_status=Booking.STATUS_PAID,
        start_time__lte=now,
        end_time__gt=now,
        slot__is_occupied=True
    ).exists():
        occupancy_status = 'OCCUPIED'

    # Group slots by level in a predictable order for the template
    slots_by_level = {}
    order = []
    for s in all_slots:
        lvl = s.level or 'Level'
        if lvl not in slots_by_level:
            slots_by_level[lvl] = []
            order.append(lvl)
        slots_by_level[lvl].append(s)

    # Produce an ordered list of (level, slots) tuples using a natural sort
    # Key: split alphabetic prefix and numeric suffix (e.g. B1 -> ('B', 1))
    def _level_sort_key(lvl):
        if not lvl:
            return ('', 0)
        m = re.match(r"^([A-Za-z]+)\s*([0-9]+)$", lvl.strip())
        if m:
            prefix = m.group(1).upper()
            num = int(m.group(2))
            return (prefix, num)
        # fallback: find first number anywhere
        m2 = re.search(r"([0-9]+)", lvl)
        if m2:
            prefix = re.sub(r"[0-9]", '', lvl).strip().upper()
            return (prefix, int(m2.group(1)))
        return (lvl.strip().upper(), 0)

    ordered_levels = sorted(list(slots_by_level.keys()), key=_level_sort_key)
    ordered_slots_by_level = [(lvl, slots_by_level[lvl]) for lvl in ordered_levels]

    return render(request, 'accounts/driver_dashboard.html', {
        'all_slots': all_slots,
        'available_slots': available_slots,
        'user_bookings': user_bookings,
        'pending_booking': pending_booking,
        'booking_form': booking_form,
        'header_title': 'Reserve Your Spot',
        'occupancy_status': occupancy_status,
        'total_slots': total_slots,
        'available_count': available_count,
        'occupied_count': occupied_count,
        'availability_percentage': availability_percentage,
        # Map slot_id -> vehicle_type when occupied (used by template to render vehicle icons)
        'slot_vehicle_types': _get_slot_vehicle_types(),
        # Pre-computed SVG layout for parking bays (x,y,w,h) grouped by level
        'svg_slots': _compute_svg_slots(all_slots),
        'slots_by_level': slots_by_level,
        'ordered_slots_by_level': ordered_slots_by_level,
    })


@login_required
def slot_statuses_api(request):
    """Return JSON with current slot statuses for client-side polling.
    Example response: [{"slot_id":"B1_01","is_occupied":true,"vehicle_type":"sedan"}, ...]
    """
    slots = ParkingSlot.objects.all().order_by('level', 'slot_id')
    data = []
    for s in slots:
        data.append({
            'slot_id': s.slot_id,
            'is_occupied': bool(s.is_occupied),
            'vehicle_type': getattr(s, 'vehicle_type', None),
        })
    return JsonResponse({'slots': data})

# --- 5. Driver: Initiate Booking ---
@login_required
def initiate_booking_view(request, slot_id):
    slot = get_object_or_404(ParkingSlot, slot_id=slot_id)

    if slot.is_occupied:
        messages.error(request, f"Slot {slot_id} is no longer available.")
        return redirect('parking:driver_slots')

    # Prevent a single user from booking multiple slots when they already
    # have an active or pending booking. If the user already has a PENDING
    # booking (awaiting payment) or a PAID booking that hasn't expired
    # (end_time > now), block new booking attempts.
    now = timezone.now()
    # Consider only recent pending bookings (e.g., last 15 minutes) as blocking.
    # This prevents very old/abandoned pending bookings from permanently blocking new bookings.
    pending_window = now - timezone.timedelta(minutes=15)
    has_pending = Booking.objects.filter(
        user=request.user,
        payment_status=Booking.STATUS_PENDING,
        created_at__gte=pending_window
    ).exists()
    # Only consider a PAID booking as "active" if it is currently in effect (start <= now < end)
    # and the linked slot is still marked occupied. This avoids future/past paid bookings from
    # blocking new bookings.
    has_active_paid = Booking.objects.filter(
        user=request.user,
        payment_status=Booking.STATUS_PAID,
        start_time__lte=now,
        end_time__gt=now,
        slot__is_occupied=True
    ).exists()
    if has_pending or has_active_paid:
        messages.error(request, "You already have an active or pending booking. You cannot book another slot until it completes or is cancelled.")
        return redirect('parking:driver_slots')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            duration_hours = form.cleaned_data.get('duration_hours', 1)

            # If end_time not provided, calculate from start_time + duration_hours
            if not end_time:
                end_time = start_time + timezone.timedelta(hours=duration_hours)

            # Prevent double-booking: check for time-overlap with existing PENDING/PAID bookings
            overlap_q = Q(payment_status__in=[Booking.STATUS_PENDING, Booking.STATUS_PAID]) & Q(slot=slot) & (
                Q(start_time__lt=end_time, end_time__gt=start_time) |
                Q(start_time__lt=end_time, end_time__isnull=True) |
                Q(start_time__isnull=True, end_time__gt=start_time)
            )
            existing = Booking.objects.filter(overlap_q)
            if existing.exists():
                messages.error(request, f"Slot {slot_id} already has a booking in that time range. Please choose another slot or time.")
                return redirect('parking:driver_slots')

            # Create booking (total_fee will be computed in Booking.save())
            booking = Booking.objects.create(
                user=request.user,
                slot=slot,
                start_time=start_time,
                end_time=end_time,
                payment_status=Booking.STATUS_PENDING
            )

            # Initiate M-Pesa STK push (simulated or real depending on settings)
            try:
                client = get_client()
                # Use booking.total_fee (Booking.save computed it) and cast to int for STK
                amount = int(round(float(booking.total_fee))) if booking.total_fee else 0
                checkout_id = client.stk_push(request.user.phone_number, amount, booking.id)
                booking.checkout_request_id = checkout_id
                booking.save()
            except Exception:
                booking.checkout_request_id = f"CHKT_{booking.id}_{datetime.now().strftime('%f')}"
                booking.save()

            messages.success(request, f"Booking initiated for {slot_id}. Payment prompt sent to {request.user.phone_number} for KES {booking.total_fee}.")
            return redirect('parking:booking_status', booking_id=booking.id)

        messages.error(request, "Invalid booking details. Check start time and duration.")
        return redirect('parking:driver_slots')

    return redirect('parking:driver_slots')

# --- 6. Booking Status View ---
@login_required
def booking_status_view(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    return render(request, 'parking/booking_status.html', {
        'booking': booking,
        'is_paid': booking.payment_status == Booking.STATUS_PAID
    })


@login_required
def booking_status_api(request, booking_id):
    """Returns JSON with the current payment status for a booking. Used by client-side polling."""
    booking = get_object_or_404(Booking, pk=booking_id)
    # Only allow the booking owner or admins to poll
    if booking.user != request.user and not is_admin(request.user):
        return JsonResponse({'error': 'forbidden'}, status=403)

    data = {
        'payment_status': booking.payment_status,
        'mpesa_receipt_no': booking.mpesa_receipt_no,
        'end_time': booking.end_time.isoformat() if booking.end_time else None,
    }
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def simulate_booking_payment(request, booking_id):
    """Test helper: mark a booking as PAID (simulate M-Pesa callback).
    This endpoint should be removed or secured in production.
    """
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.method == 'POST':
        booking.payment_status = Booking.STATUS_PAID
        booking.mpesa_receipt_no = f"SIM-{booking.id}-{timezone.now().strftime('%f')}"
        booking.save()
        # Mark slot occupied now that payment succeeded
        slot = booking.slot
        slot.is_occupied = True
        slot.save()
        messages.success(request, f"Booking {booking_id} marked as PAID (simulated).")
    return redirect('parking:admin_booking_list')


@login_required
def cancel_booking_view(request, booking_id):
    """Allow a driver to cancel a pending booking and release any holds."""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    if request.method == 'POST':
        if booking.payment_status == Booking.STATUS_PENDING:
            booking.payment_status = Booking.STATUS_FAILED
            booking.save()
            messages.info(request, f"Booking {booking_id} has been cancelled.")
        else:
            messages.error(request, "Only pending bookings can be cancelled.")
    return redirect('parking:driver_slots')


@login_required
def past_reservations_view(request):
    """Show driver their past reservations (paid or failed) ordered by most recent."""
    bookings = Booking.objects.filter(user=request.user).exclude(payment_status=Booking.STATUS_PENDING).order_by('-created_at')
    return render(request, 'accounts/past_reservations.html', {'bookings': bookings, 'header_title': 'Past Reservations'})


@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def admin_activities_view(request):
    """Show recent admin actions using Django's LogEntry model."""
    try:
        from django.contrib.admin.models import LogEntry
        activities = LogEntry.objects.select_related('user').order_by('-action_time')[:200]
    except Exception:
        activities = []
    # Compute simple booking/activity statistics for today
    today = timezone.localdate()
    bookings_today_qs = Booking.objects.filter(created_at__date=today)
    bookings_today = bookings_today_qs.count()
    revenue_today = bookings_today_qs.filter(payment_status=Booking.STATUS_PAID).aggregate(total=Sum('total_fee'))['total'] or 0

    # Bookings per hour (0-23)
    bookings_by_hour = []
    for h in range(24):
        cnt = bookings_today_qs.filter(created_at__hour=h).count()
        bookings_by_hour.append({'hour': h, 'count': cnt})
    # Determine peak hour
    peak_hour = None
    peak_count = 0
    if bookings_by_hour:
        peak = max(bookings_by_hour, key=lambda x: x['count'])
        peak_hour = peak.get('hour')
        peak_count = peak.get('count', 0)

    context = {
        'activities': activities,
        'header_title': 'Admin Activities',
        'bookings_today': bookings_today,
        'revenue_today': revenue_today,
        'bookings_by_hour': bookings_by_hour,
        'peak_hour': peak_hour,
        'peak_count': peak_count,
    }
    return render(request, 'parking/admin_activities.html', context)

# --- 7. Driver: Slot Detail View ---
@login_required
def slot_detail_view(request, slot_id):
    slot = get_object_or_404(ParkingSlot, slot_id=slot_id)
    booking_form = BookingForm()

    return render(request, 'parking/slot_detail.html', {
        'slot': slot,
        'booking_form': booking_form,
        'header_title': f'Slot {slot_id} Details'
    })


@login_required
def leave_slot_view(request):
    """Allow a driver to indicate they are leaving their occupied slot.
    This will set the booking end_time to now and mark the slot as free.
    """
    if request.method == 'POST':
        now = timezone.now()
        # Find the most recent PAID booking for this user that is associated with an
        # occupied slot. Do not require end_time comparison here — if the slot is
        # marked occupied we should allow the user to free it regardless of timestamps.
        booking = Booking.objects.filter(
            user=request.user,
            payment_status=Booking.STATUS_PAID,
            slot__is_occupied=True
        ).order_by('-created_at').first()

        if not booking:
            messages.error(request, "No active occupied slot found to leave.")
            return redirect('parking:driver_slots')

        # Store previous end_time and booking id in session to allow undo
        prev_end = booking.end_time.isoformat() if booking.end_time else None
        request.session['last_leave'] = {
            'booking_id': booking.id,
            'previous_end_time': prev_end,
            'slot_id': booking.slot.slot_id,
            'timestamp': now.isoformat()
        }

        # Mark booking as ended now and free the slot
        booking.end_time = now
        booking.save()

        slot = booking.slot
        slot.is_occupied = False
        slot.save()

        messages.success(request, f"You have left slot {slot.slot_id}. You can undo this action briefly from the dashboard.")
    return redirect('parking:driver_slots')


@login_required
def undo_leave_view(request):
    """Restore the most recent leave action saved in session (if any).
    This will reapply the previous booking end_time and mark the slot occupied.
    """
    last = request.session.get('last_leave')
    if not last:
        messages.error(request, "No recent leave action to undo.")
        return redirect('parking:driver_slots')

    booking_id = last.get('booking_id')
    try:
        booking = Booking.objects.get(pk=booking_id, user=request.user)
    except Booking.DoesNotExist:
        messages.error(request, "Cannot undo: booking not found.")
        request.session.pop('last_leave', None)
        return redirect('parking:driver_slots')

    # Restore previous end_time if available, else clear it
    prev = last.get('previous_end_time')
    if prev:
        booking.end_time = timezone.datetime.fromisoformat(prev)
    else:
        booking.end_time = None
    booking.save()

    slot = booking.slot
    slot.is_occupied = True
    slot.save()

    # Clear the session undo record
    request.session.pop('last_leave', None)
    messages.success(request, f"Leave action undone. Slot {slot.slot_id} is marked occupied again.")
    return redirect('parking:driver_slots')
