from django.apps import AppConfig

class AccountsConfig(AppConfig):
    """
    Configuration class for the 'accounts' application. 
    This is required by Django when the app is listed in settings.py.
    """
    # The default auto field type
    default_auto_field = 'django.db.models.BigAutoField'
    
    # The short name for the application
    name = 'accounts'
    
    # Human-readable name
    verbose_name = 'User Accounts & Authentication'