from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, LoginForm 

# --- 1. Registration View: Handles New Account Creation ---
def register_view(request):
    """
    Handles both GET (display form) and POST (submit form) for user registration.
    Registers a new user (Driver) and redirects them based on role.
    """
    if request.method == 'POST':
        # Populate the form with submitted data from the HTML form
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # If form validation passes, save the new user model instance
            user = form.save()
            
            # Log the user in immediately after successful registration
            login(request, user)
            messages.success(request, f'Welcome aboard, {user.username}! Your account has been created.')
            
            # Redirect user based on their role (Admin or Driver)
            # is_staff or is_superuser flags denote an Administrator
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard') 
            return redirect('driver_dashboard') 
        else:
            # If form is invalid, display a generic error message
            messages.error(request, 'Error creating account. Please check your inputs.')
            # The template will display the specific field errors
    else:
        # For GET request, display an empty registration form
        form = RegistrationForm()
        
    return render(request, 'accounts/register.html', {'form': form})


def home_view(request):
    """Simple homepage view for verifying template loading at root URL ('/')."""
    from parking.models import ParkingSlot
    
    # Get all parking slots
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
    return render(request, 'accounts/home.html', context)
    from parking.models import ParkingSlot
    
    # Get all parking slots
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
    return render(request, 'accounts/home.html', context)

# --- 2. Login View: Handles User Authentication ---
def login_view(request):
    """
    Handles user login, validates credentials using LoginForm, and creates a session.
    Redirects user to the appropriate dashboard (Admin or Driver).
    """
    if request.method == 'POST':
        # Pass the request and submitted data to the LoginForm
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            # Retrieve the authenticated user object from the form
            user = form.get_user()
            
            # Start the user session
            login(request, user) 
            messages.success(request, f'Welcome back, {user.username}!')

            # Redirect based on user role
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard') 
            return redirect('driver_dashboard')
        else:
            # Handle invalid credentials (e.g., incorrect email or password)
            messages.error(request, 'Invalid email or password.')
    else:
        # For GET request, display an empty login form
        form = LoginForm()
        
    return render(request, 'accounts/login.html', {'form': form})

# --- 3. Logout View: Ends Session ---
@login_required 
def logout_view(request):
    """
    Logs the currently authenticated user out and destroys the session.
    The @login_required decorator prevents unauthenticated users from accessing this.
    """
    logout(request)
    messages.info(request, "You have been logged out!")
    return redirect('login')
    
# --- 4. Placeholder Dashboard Views (for Redirection Logic) ---

@login_required
def driver_dashboard(request):
    """ 
    Driver dashboard showing available parking slots. 
    This is where drivers can view and reserve slots. 
    """
    return render(request, 'parking/driver_available_slots.html', {})

@login_required
def admin_dashboard(request):
    """ 
    Admin dashboard showing parking slots management. 
    Crucially, it checks for administrative privileges before rendering.
    """
    # Security check: Ensure the logged-in user is staff or superuser
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access Denied. You do not have permission to access the Admin dashboard.")
        # Fallback to the driver dashboard if access is denied
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
        
    # If the user is an admin, render the admin dashboard
    return render(request, 'accounts/admin_dashboard.html', context)