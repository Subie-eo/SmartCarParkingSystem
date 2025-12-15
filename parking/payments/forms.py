from django import forms

class PaymentForm(forms.Form):
    # Placeholder: in many MPesa flows you don't need additional fields
    # because payment is initiated server-side and the user confirms on phone.
    pass
