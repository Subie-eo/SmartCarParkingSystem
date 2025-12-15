from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# Get the custom User model defined in accounts/models.py
User = get_user_model()

# --- 1. Registration Form ---
class RegistrationForm(UserCreationForm):
    """
    Form for user registration (Driver account creation). 
    
    It inherits from Django's built-in UserCreationForm to ensure secure 
    handling of password hashing and confirmation logic. It adds the 
    application-specific fields required for the parking system.
    """
    
    # Required custom field for M-Pesa integration (phone number)
    phone_number = forms.CharField(
        max_length=15, 
        label='M-Pesa Phone Number', 
        required=True,
        help_text='Used for payment processing (STK Push).'
    )
    
    # Required custom field for vehicle identification
    vehicle_plate = forms.CharField(
        max_length=20, 
        label='Vehicle Plate Number', 
        required=True,
        help_text='The unique identifier for the vehicle.'
    )

    class Meta(UserCreationForm.Meta):
        # Explicitly link the form to our custom User model
        model = User
        # Define all fields that should appear in the registration form
        fields = UserCreationForm.Meta.fields + ('email', 'phone_number', 'vehicle_plate')
    
    def save(self, commit=True):
        """
        Overrides the default save method to set the user's default role before saving.
        """
        # Call the parent save method to get the user instance without committing to DB yet
        user = super().save(commit=False)
        
        # Ensure the user is designated as a regular driver by default
        # 'is_driver' is implemented as a read-only property on the model, so
        # set the underlying role flags instead.
        user.is_staff = False
        user.is_superuser = False
        
        # Sanitize the email address for consistent storage
        if user.email:
            user.email = user.email.lower()
            
        # Commit the changes to the database if required
        if commit:
            user.save()
        return user

# --- 2. Login Form ---
class LoginForm(AuthenticationForm):
    """
    Standard Django form for user login.
    
    It handles the core authentication process (checking credentials and creating a session).
    It is customized to use 'Email' instead of the default 'Username' label.
    """
    # Override the default 'username' field to display 'Email' and accept email input
    username = forms.CharField(
        label='Email',
        max_length=254,
        # Use an email widget and apply styling classes
        widget=forms.EmailInput(attrs={
            'autofocus': True, 
            'class': 'w-full p-2 border border-gray-300 rounded-lg'
        })
    )
    
    # Customize password widget for consistent styling
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg'
        })
    )
    
    # The inherited AuthenticationForm handles the rest of the login logic (clean(), confirm_login_allowed(), etc.)
    pass