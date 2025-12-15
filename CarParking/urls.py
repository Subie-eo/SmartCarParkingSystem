from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts.views import home_view

urlpatterns = [
    # 1. Project Homepage Route
    path('', home_view, name='home'),
    
    # 2. Django Admin Interface Route
    path('admin/', admin.site.urls),
    
    # 3. Application Inclusion: Authentication Module
    # Routes all custom authentication/dashboard URLs (register, login, etc.) 
    # to the accounts application's urls.py
    path('accounts/', include('accounts.urls')), 
    
    # 4. Application Inclusion: Core Parking Module
    # Routes all core business logic URLs (slots, booking) to the parking application's urls.py
    path('parking/', include('parking.urls')), 
    
    # --- Django Password Reset System (Custom Templates) ---
    # These remain in the main file as they are general project utility routes.
    
    # A. Reset Form (Step 1: Request email)
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/accounts/password_reset/done/'
    ), name='password_reset'),
    
    # B. Reset Done (Step 2: Confirmation message after sending email)
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    
    # C. Reset Confirm (Step 3: User sets new password after clicking email link)
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/reset/complete/'
    ), name='password_reset_confirm'),
    
    # D. Reset Complete (Step 4: Final confirmation after setting new password)
    path('accounts/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
]