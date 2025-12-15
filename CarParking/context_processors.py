from django.conf import settings

def site_settings(request):
    """Expose SITE_NAME and contact info to all templates.

    Returns a dict with `SITE_NAME` and `CONTACT_INFO` keys. CONTACT_INFO is a dict
    with keys `company_name`, `email`, `phone`, and `address`. If no ContactInfo
    exists in the database, sensible defaults are returned.
    """
    contact = None
    try:
        # Import locally to avoid circular import at startup
        from .models import ContactInfo
        contact = ContactInfo.objects.order_by('-updated_at').first()
    except Exception:
        contact = None

    if contact:
        contact_info = {
            'company_name': contact.company_name,
            'email': contact.email,
            'phone': contact.phone,
            'address': contact.address,
        }
    else:
        contact_info = {
            'company_name': getattr(settings, 'SITE_NAME', 'SmartPark'),
            'email': 'info@smartpark.example',
            'phone': '+1-555-0100',
            'address': '123 Parking Lane, YourCity',
        }

    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'SmartPark'),
        'CONTACT_INFO': contact_info,
        'ASSET_VERSION': getattr(settings, 'ASSET_VERSION', '1'),
    }
