from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from ..models import Booking, ParkingSlot

@login_required
def payment_pending_view(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    return render(request, 'payments/payment_pending.html', {'booking': booking})

@login_required
def payment_success_view(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    return render(request, 'payments/payment_successful.html', {'booking': booking})

@login_required
def payment_failed_view(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    return render(request, 'payments/payment_failed.html', {'booking': booking})

@csrf_exempt
def mpesa_callback(request):
    """Simple webhook endpoint for MPesa sandbox callbacks.
    This expects JSON payloads; in production you must validate the source and
    secure this endpoint (e.g., use a shared secret, HTTPS, and verify signatures).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        booking_id = payload.get('booking_id') or payload.get('MerchantRequestID') or payload.get('CheckoutRequestID')
        receipt = payload.get('receipt') or payload.get('MpesaReceiptNumber')
        # Determine success heuristics (sandbox formats vary)
        status = payload.get('status') or payload.get('ResultCode')

        if not booking_id:
            return JsonResponse({'error': 'missing booking_id'}, status=400)

        booking = Booking.objects.get(pk=booking_id)

        # Consider numeric 0 or string '0' as success in Safaricom callback
        success = False
        if status in (0, '0'):
            success = True
        elif isinstance(status, str) and status.lower() in ('success', 'ok'):
            success = True

        if success:
            booking.payment_status = Booking.STATUS_PAID
            booking.mpesa_receipt_no = receipt or f"MPESA-{booking_id}"
            booking.save()
            slot = booking.slot
            slot.is_occupied = True
            slot.save()
            return JsonResponse({'ok': True})

        # Non-success
        booking.payment_status = Booking.STATUS_FAILED
        booking.save()
        return JsonResponse({'ok': False})

    except Booking.DoesNotExist:
        return JsonResponse({'error': 'booking not found'}, status=404)
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)
