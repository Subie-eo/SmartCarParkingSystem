from django.apps import AppConfig

class ParkingConfig(AppConfig):
    """
    Configuration class for the 'parking' application.
    This file is essential for Django to properly recognize and load the application
    when running management commands (like makemigrations).
    """
    # Use the default primary key field type
    default_auto_field = 'django.db.models.BigAutoField'
    
    # The short name used for the application in INSTALLED_APPS and routing
    name = 'parking'
    
    # Human-readable name displayed in the Django Admin interface
    verbose_name = 'Parking Slot & Booking Management'