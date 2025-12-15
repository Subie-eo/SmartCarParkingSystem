from django.apps import AppConfig


class CarParkingConfig(AppConfig):
    """Configuration class for the project app.

    The package `CarParking` contains the models, views and forms used
    by the project. This AppConfig name and `name` value must match the
    actual package to be importable by Django.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'CarParking'
    verbose_name = 'Car Parking'