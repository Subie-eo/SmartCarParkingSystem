from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# Get the custom User model defined in settings.py
User = get_user_model()

# ------------------------------------------------
# 1. Registration Form
# ------------------------------------------------
class RegistrationForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=15,
        label='M-Pesa Phone Number',
        required=True,
        help_text='Used for payment processing (STK Push).'
    )
    
    vehicle_plate = forms.CharField(
        max_length=20,
        label='Vehicle Plate Number',
        required=True,
        help_text='The unique identifier for the vehicle.'
    )

    VEHICLE_TYPE_CHOICES = (
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('pickup', 'Pickup'),
        ('motorcycle', 'Motorcycle'),
    )

    vehicle_type = forms.ChoiceField(
        choices=VEHICLE_TYPE_CHOICES,
        label='Vehicle Type',
        required=False,
        help_text='Select the vehicle type for suitable slot suggestions.'
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Explicitly declare fields to avoid surprises with a custom USERNAME_FIELD.
        # Include password1/password2 from UserCreationForm for password entry/validation.
        fields = ('username', 'email', 'phone_number', 'vehicle_plate', 'vehicle_type', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Ensure role flags for regular drivers
        user.is_staff = False
        user.is_superuser = False
        # Normalize email
        if user.email:
            user.email = user.email.lower()
        # If username is missing for any reason, derive it from email local-part
        if not getattr(user, 'username', None):
            if user.email:
                user.username = user.email.split('@')[0]
            else:
                user.username = ''
        if commit:
            # store vehicle_type if provided
            vt = self.cleaned_data.get('vehicle_type')
            if vt:
                user.vehicle_type = vt
            user.save()
        return user

# ------------------------------------------------
# 2. Login Form
# ------------------------------------------------
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'class': 'w-full p-2 border border-gray-300 rounded-lg'
        })
    )
    
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg'
        })
    )

# ------------------------------------------------
# 3. Driver Update Form
# ------------------------------------------------
class DriverUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'vehicle_plate', 'vehicle_type']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'vehicle_plate': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'vehicle_type': forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_vehicle_plate(self):
        plate = self.cleaned_data.get('vehicle_plate').upper()
        qs = User.objects.filter(vehicle_plate__iexact=plate).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This vehicle plate is already registered.")
        return plate
