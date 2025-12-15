import uuid
import threading
import time
from django.conf import settings

# Simple local Mpesa STK Push client for development/testing.
# In production this module should perform OAuth and call Safaricom's API endpoints.

class MpesaClient:
    def __init__(self):
        self.simulate = getattr(settings, 'MPESA_SIMULATE', True)

    def stk_push(self, phone_number: str, amount: float, booking_id: int) -> str:
        """Initiate an STK push for `amount` to `phone_number` linked to booking_id.
        Returns a checkout_request_id string. In simulate mode this also schedules
        a background task that marks the booking PAID after a short delay.
        """
        checkout_request_id = f"STK_{booking_id}_{uuid.uuid4().hex[:8]}"

        if self.simulate:
            # Schedule a simulated confirmation after delay (5 seconds)
            def _confirm():
                try:
                    # Import models lazily to avoid import cycles
                    from .models import Booking
                    from django.utils import timezone
                    b = Booking.objects.get(pk=booking_id)
                    b.payment_status = Booking.STATUS_PAID
                    b.mpesa_receipt_no = f"SIM-{booking_id}-{int(time.time())}"
                    # ensure end_time exists (keep previous if set)
                    if not b.end_time:
                        b.end_time = timezone.now() + (b.end_time - b.start_time if b.end_time else timezone.timedelta(hours=1))
                    b.save()
                    # mark slot occupied
                    slot = b.slot
                    slot.is_occupied = True
                    slot.save()
                except Exception:
                    # best-effort simulation; ignore exceptions
                    pass

            t = threading.Timer(5.0, _confirm)
            t.daemon = True
            t.start()
        else:
            # Real implementation placeholder: perform OAuth, then STK push.
            # Should set checkout_request_id from Safaricom response.
            # For now, we only return a generated id.
            pass

        return checkout_request_id


# Convenience factory
def get_client():
    return MpesaClient()
