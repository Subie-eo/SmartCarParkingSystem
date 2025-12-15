"""
accounts.views
----------------
Authentication and user-facing account views.

This module contains registration/login/logout and the driver's dashboard
as well as small utilities like subscription handling. Views perform
lightweight orchestration and delegate domain work to models/forms.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from accounts.forms import RegistrationForm, LoginForm, DriverUpdateForm
from parking.models import ParkingSlot, Booking
from parking.models import Subscription
from parking.forms import BookingForm
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
import os
from pathlib import Path

# ------------------------------------------------
# 1. Registration View
# ------------------------------------------------
def register_view(request):
    """
    Handles new driver registration.
    Automatically logs in the user after successful registration.
    Redirects staff/superuser to admin dashboard.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome aboard, {user.username}! Your account has been created.')
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('driver_dashboard')
        else:
            # Display field-specific errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


# ------------------------------------------------
# 2. Homepage View
# ------------------------------------------------
def home_view(request):
    """Renders the homepage for unauthenticated users.
    
    Authenticated admins are redirected to the admin dashboard.
    Authenticated drivers are redirected to the driver dashboard.
    """
    # If user is authenticated, redirect them to their dashboard
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('driver_dashboard')
    
    return render(request, 'accounts/home.html', {})


# ------------------------------------------------
# 3. Login View
# ------------------------------------------------
def login_view(request):
    """
    Handles user login using email and password.
    Redirects to admin dashboard for staff/superuser.
    """
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('driver_dashboard')
        else:
            # Display field-specific errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


# ------------------------------------------------
# 4. Logout View
# ------------------------------------------------
@login_required
def logout_view(request):
    """Logs out the current user."""
    logout(request)
    messages.info(request, "You have been logged out!")
    return redirect('home')


# ------------------------------------------------
# 5. Driver Dashboard
# ------------------------------------------------
@login_required
def driver_dashboard(request):
    """
    Displays all parking slots for drivers with their current status.
    Also provides booking form to reserve available slots.
    """
    # Get ALL slots so drivers can see the full parking layout with states
    all_slots = ParkingSlot.objects.all().order_by('level', 'slot_id')
    available_slots = ParkingSlot.objects.filter(is_occupied=False).order_by('level', 'slot_id')
    booking_form = BookingForm()

    # Get driver's recent bookings
    user_bookings = Booking.objects.filter(user=request.user).order_by('-start_time')[:5]

    # Determine user's occupancy status: PENDING (awaiting payment), OCCUPIED (paid), or FREE
    now = timezone.now()
    occupancy_status = 'FREE'
    if Booking.objects.filter(user=request.user, payment_status=Booking.STATUS_PENDING).exists():
        occupancy_status = 'PENDING'
    elif Booking.objects.filter(user=request.user, payment_status=Booking.STATUS_PAID, end_time__gte=now).exists():
        occupancy_status = 'OCCUPIED'

    # Calculate parking statistics
    total_slots = all_slots.count()
    occupied_count = ParkingSlot.objects.filter(is_occupied=True).count()
    available_count = total_slots - occupied_count
    availability_percentage = (available_count / total_slots * 100) if total_slots > 0 else 0

    # To keep a single canonical dashboard route, redirect to the parking app's
    # `driver_slots` view which renders the same `accounts/driver_dashboard.html`.
    from django.shortcuts import redirect
    return redirect('parking:driver_slots')


# ------------------------------------------------
# 6. Admin Dashboard
# ------------------------------------------------
@login_required
def admin_dashboard(request):
    """
    Admin dashboard showing parking management overview.
    Non-admins are redirected to the driver dashboard.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access Denied. You do not have permission to access the Admin dashboard.")
        return redirect('driver_dashboard')
    
    # Get parking statistics
    from parking.models import ParkingSlot
    all_slots = ParkingSlot.objects.all()
    total_slots = all_slots.count()
    occupied_count = all_slots.filter(is_occupied=True).count()
    available_count = total_slots - occupied_count
    availability_percentage = (available_count / total_slots * 100) if total_slots > 0 else 0
    
    context = {
        'total_slots': total_slots,
        'occupied_count': occupied_count,
        'available_count': available_count,
        'availability_percentage': availability_percentage,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)


# ------------------------------------------------
# 7. Driver Profile Update View
# ------------------------------------------------
@login_required
def driver_update_profile(request):
    """
    Allows a logged-in driver to update their account details.
    Excludes password updates.
    """
    if request.method == 'POST':
        # Handle account deletion action
        if 'delete_account' in request.POST:
            user = request.user
            # capture username/email for message
            uname = getattr(user, 'username', str(user))
            # delete and logout
            user.delete()
            messages.info(request, f"We're sorry to see you go, {uname}. We hope you'll come back soon.")
            return redirect('home')

        form = DriverUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('driver_dashboard')
        else:
            # Display field-specific errors only
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = DriverUpdateForm(instance=request.user)

    context = {
        'form': form,
        'header_title': 'Update Your Profile'
    }
    return render(request, 'accounts/driver_update_profile.html', context)


def subscribe_view(request):
    """Handle newsletter subscription from homepage."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            # If AJAX request, return JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Please provide a valid email address.'}, status=400)
            messages.error(request, 'Please provide a valid email address.')
            return redirect('home')
        try:
            sub, created = Subscription.objects.get_or_create(email=email)
            if created:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Thanks — you have been subscribed.'})
                messages.success(request, 'Thanks — you have been subscribed.')
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'This email is already subscribed.'})
                messages.info(request, 'This email is already subscribed.')
        except Exception as exc:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': f'Unable to subscribe: {exc}'} , status=500)
            messages.error(request, f'Unable to subscribe: {exc}')
    # Fallback redirect for non-AJAX submissions
    return redirect('home')


# --------------------------
# Development: Sent Emails
# --------------------------
def _is_staff(user):
    return user.is_staff or user.is_superuser


@user_passes_test(_is_staff)
def sent_emails_list(request):
    """Lists files written by the file-based email backend for debugging."""
    # Only enable in DEBUG to avoid exposing files in production
    if not getattr(settings, 'DEBUG', False):
        return JsonResponse({'error': 'Not available in production'}, status=403)

    file_path = getattr(settings, 'EMAIL_FILE_PATH', None)
    if not file_path:
        # Try default
        file_path = Path(settings.BASE_DIR) / 'sent_emails'
    file_path = Path(file_path)
    files = []
    if file_path.exists():
        for p in sorted(file_path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.is_file():
                files.append({
                    'name': p.name,
                    'size': p.stat().st_size,
                    'mtime': p.stat().st_mtime,
                })

    return render(request, 'accounts/sent_emails_list.html', {'files': files})


@user_passes_test(_is_staff)
def sent_email_detail(request, filename):
    """Show contents of a saved email file."""
    if not getattr(settings, 'DEBUG', False):
        return JsonResponse({'error': 'Not available in production'}, status=403)

    file_path = getattr(settings, 'EMAIL_FILE_PATH', None)
    if not file_path:
        file_path = Path(settings.BASE_DIR) / 'sent_emails'
    file_path = Path(file_path) / filename
    if not file_path.exists() or not file_path.is_file():
        return JsonResponse({'error': 'Not found'}, status=404)

    content = file_path.read_text(encoding='utf-8', errors='replace')
    return render(request, 'accounts/sent_email_detail.html', {'filename': filename, 'content': content})
