from django.urls import path
from .views import register_view, login_view, logout_view, driver_dashboard, admin_dashboard
from . import views

# NOTE: The password reset views are handled in the main CarParking/urls.py file.

urlpatterns = [
    # --- Core Authentication URLs (Prefixed by /accounts/) ---
    
    # Full URL: /accounts/register/
    path('register/', register_view, name='register'), 
    
    # Full URL: /accounts/login/
    path('login/', login_view, name='login'),         
    
    # Full URL: /accounts/logout/
    path('logout/', logout_view, name='logout'),       
    
    # --- Dashboard Redirection URLs (Require Login) ---
    
    # Full URL: /accounts/dashboard/driver/
    path('dashboard/driver/', driver_dashboard, name='driver_dashboard'), 
    
    # Full URL: /accounts/dashboard/admin/
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),   

    path('driver/update/', views.driver_update_profile, name='driver_update'),
    path('subscribe/', views.subscribe_view, name='subscribe'),
    # Development helpers: view saved email files
    path('sent-emails/', views.sent_emails_list, name='sent_emails'),
    path('sent-emails/<path:filename>/', views.sent_email_detail, name='sent_email_detail'),
]