from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from CarParking.models import User

# --- Custom Admin Class for User Model ---
class CustomUserAdmin(UserAdmin):
    """
    Customizes the Django Admin interface for the custom User model.
    Ensures new fields (phone_number, vehicle_plate, is_driver) are displayed and editable.
    """
    list_display = (
        'email',
        'username',
        'phone_number',
        'vehicle_plate',
        'is_staff',
        'is_active',
    )

    search_fields = ('email', 'username', 'phone_number', 'vehicle_plate')

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'vehicle_plate')}),
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Parking Details', {'fields': ('phone_number', 'vehicle_plate')}),
    )

# Register the custom User model with the custom admin class
admin.site.register(User, CustomUserAdmin)
