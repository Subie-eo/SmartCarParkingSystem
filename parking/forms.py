from django import forms
from .models import ParkingSlot, Booking
from django.forms import DateTimeInput
from django.core.exceptions import ValidationError
from datetime import timedelta

# --- 1. Parking Slot Management Form (Admin CRUD) ---
class ParkingSlotForm(forms.ModelForm):
    """
    Form used by Administrators to create, update, and manage ParkingSlot entities.
    This form corresponds to the Admin CRUD requirement for the inventory.
    """
    class Meta:
        model = ParkingSlot
        # Fields that the admin needs to manage the spot
        fields = ['slot_id', 'slot_name', 'level', 'pricing_category', 'is_occupied']
        labels = {
            'slot_id': 'Slot Identifier (e.g., A-101)',
            'slot_name': 'Descriptive Name',
            'level': 'Level/Floor',
            'pricing_category': 'Pricing Rate',
            'is_occupied': 'Currently Occupied?'
        }
        widgets = {
            # Provide a clear placeholder for the unique identifier
            'slot_id': forms.TextInput(attrs={'placeholder': 'E.g., B-205'}),
        }
        
    def clean_is_occupied(self):
        """
        Custom validation hook for the 'is_occupied' status.
        Ensures any manual change is intentional (reserved for future, complex admin logic).
        """
        is_occupied = self.cleaned_data.get('is_occupied')
        # Simple placeholder logic: return the cleaned value.
        return is_occupied

# --- 2. Booking Form (Driver Interface) ---
class BookingForm(forms.ModelForm):
    """
    Form used by Drivers to specify reservation time and duration before M-Pesa payment.
    """
    # Custom field: duration in hours. This is not a direct model field but is 
    # used to calculate the Booking model's 'end_time'.
    duration_hours = forms.IntegerField(
        min_value=1, 
        max_value=24, 
        initial=2,
        label='Duration (hours)',
        help_text='Enter duration in hours (max 24).'
    )

    class Meta:
        model = Booking
        # We only ask the user for the start time; the view sets the user/slot and calculates total_fee.
        fields = ['start_time'] 
        labels = {
            'start_time': 'Start Time of Reservation',
        }
        widgets = {
            # Use HTML5 datetime-local input for better user experience on modern browsers
            'start_time': DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        
    def clean(self):
        """
        Performs cross-field validation to ensure start time and duration are valid.
        Also calculates the end time for the view to use.
        """
        cleaned_data = super().clean()
        
        start_time = cleaned_data.get('start_time')
        duration_hours = cleaned_data.get('duration_hours')

        if start_time and duration_hours:
            
            # Calculate the reservation end time
            end_time = start_time + timedelta(hours=duration_hours)
            
            # Validation 1: Ensure reservation doesn't start in the past
            from django.utils import timezone
            if start_time < (timezone.now() - timedelta(minutes=5)):
                # Allowing a small buffer (5 min) for immediate bookings
                raise ValidationError("Reservation start time cannot be in the past.")

            # Validation 2: Ensure booking ends after it starts
            if end_time <= start_time:
                raise ValidationError("Reservation duration must be at least one hour.")
                
            # Store the calculated end time in cleaned_data for the view to access and save to the model
            cleaned_data['end_time'] = end_time

        return cleaned_data


# --- 3. Pricing Form (Admin) ---
class PricingForm(forms.Form):
    regular_rate = forms.DecimalField(max_digits=8, decimal_places=2, label='Regular (KES)', min_value=0)
    premium_rate = forms.DecimalField(max_digits=8, decimal_places=2, label='Premium (KES)', min_value=0)
    vip_rate = forms.DecimalField(max_digits=8, decimal_places=2, label='VIP (KES)', min_value=0)

    def clean(self):
        cleaned = super().clean()
        # Additional validation could go here; keep simple for now
        return cleaned