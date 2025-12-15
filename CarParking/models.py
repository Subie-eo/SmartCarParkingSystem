from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# --- 1. Custom User Manager ---
class UserManager(BaseUserManager):
    """
    Manager for the custom User model.
    Handles creation of users and superusers.
    """
    def create_user(self, email, username, phone_number, vehicle_plate, password=None, vehicle_type=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        if not phone_number:
            raise ValueError("Users must have a phone number")
        if not vehicle_plate:
            raise ValueError("Users must have a vehicle plate number")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            phone_number=phone_number,
            vehicle_plate=vehicle_plate,
            vehicle_type=vehicle_type,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, phone_number, vehicle_plate, password=None, vehicle_type=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email=email,
            username=username,
            phone_number=phone_number,
            vehicle_plate=vehicle_plate,
            vehicle_type=vehicle_type,
            password=password,
            **extra_fields
        )

# --- 2. Custom User Model ---
class User(AbstractUser):
    """
    Custom User model for CarParking Management System.
    Email is used as the primary login identifier.
    """
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="M-Pesa Phone Number"
    )
    vehicle_plate = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Vehicle Plate Number"
    )

    VEHICLE_TYPE_CHOICES = (
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('pickup', 'Pickup'),
        ('motorcycle', 'Motorcycle'),
    )

    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name='Vehicle Type'
    )

    # Use email instead of username for login
    USERNAME_FIELD = 'email'
    email = models.EmailField(unique=True)
    REQUIRED_FIELDS = ['username', 'phone_number', 'vehicle_plate']

    # Attach custom manager
    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_driver(self):
        """
        Returns True if the user is a driver (not staff, not superuser).
        Useful for display in Django Admin or role checks.
        """
        return not self.is_staff and not self.is_superuser

    class Meta:
        verbose_name = 'User Account'
        verbose_name_plural = 'User Accounts'


# Admin-editable contact information shown in the site footer
class ContactInfo(models.Model):
    company_name = models.CharField(max_length=200, default='SmartPark')
    email = models.EmailField(blank=True, default='info@smartpark.example')
    phone = models.CharField(max_length=50, blank=True, default='+1-555-0100')
    address = models.TextField(blank=True, default='123 Parking Lane, YourCity')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

    class Meta:
        verbose_name = 'Contact Information'
        verbose_name_plural = 'Contact Information'
