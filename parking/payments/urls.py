from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pending/<int:booking_id>/', views.payment_pending_view, name='pending'),
    path('success/<int:booking_id>/', views.payment_success_view, name='success'),
    path('failed/<int:booking_id>/', views.payment_failed_view, name='failed'),
    path('callback/', views.mpesa_callback, name='callback'),
]
