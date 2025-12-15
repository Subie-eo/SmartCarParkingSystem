from django.urls import path, include
from . import views

# Define the namespace for use in templates (e.g., href="{% url 'parking:driver_slots' %}")
app_name = 'parking'

urlpatterns = [
    # --- Driver Endpoints (Prefixed by /parking/) ---
    
    # URL: /parking/slots/ (View available slots, maps to the Driver Dashboard core feature)
    path('slots/', views.available_slots_view, name='driver_slots'),
    # Slot detail (driver-facing) - shows slot info and booking form (fallback for no-JS)
    path('slots/<str:slot_id>/', views.slot_detail_view, name='slot_detail'),
    
    # URL: /parking/book/A-101/ (Initiate booking and payment for a specific slot)
    path('book/<str:slot_id>/', views.initiate_booking_view, name='initiate_booking'),
    path('leave/', views.leave_slot_view, name='leave_slot'),
    path('leave/undo/', views.undo_leave_view, name='undo_leave'),
    
    # URL: /parking/status/123/ (View status of a specific booking, awaiting M-Pesa callback)
    path('status/<int:booking_id>/', views.booking_status_view, name='booking_status'),
    path('cancel/<int:booking_id>/', views.cancel_booking_view, name='cancel_booking'),
    path('my/reservations/', views.past_reservations_view, name='past_reservations'),
    # Payment pages and webhook now served by top-level `parkingpayments` package
    path('payment/', include('parkingpayments.urls')),
    
    # --- Admin CRUD Endpoints (Prefixed by /parking/) ---
    
    # URL: /parking/admin/slots/ (List all slots and handle creation of new slots)
    path('admin/slots/', views.slot_list_create_view, name='admin_slot_list'),
    
    # URL: /parking/admin/slots/A-101/edit/ (Update or Delete a specific slot)
    path('admin/slots/<str:slot_id>/edit/', views.slot_update_delete_view, name='admin_slot_detail'),
    # URL: /parking/admin/slots/A-101/toggle/ (Toggle the occupied status of a specific slot)
    path('admin/slots/<str:slot_id>/toggle/', views.toggle_slot_status, name='admin_slot_toggle'),
    
    # URL: /parking/admin/bookings/ (Read all reservations for monitoring)
    path('admin/bookings/', views.admin_booking_list_view, name='admin_booking_list'),
    path('admin/activities/', views.admin_activities_view, name='admin_activities'),
    path('admin/pricing/', views.pricing_rates_view, name='admin_pricing'),
    # API endpoint to poll booking status (used by client-side JS)
    path('api/booking_status/<int:booking_id>/', views.booking_status_api, name='booking_status_api'),
    # Simulation endpoint to mark booking paid (for testing only)
    path('admin/bookings/<int:booking_id>/simulate_pay/', views.simulate_booking_payment, name='simulate_booking_payment'),
    # API: current status of all slots (for live dashboard updates)
    path('api/slot_statuses/', views.slot_statuses_api, name='slot_statuses_api'),
]