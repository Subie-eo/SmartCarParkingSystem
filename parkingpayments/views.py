from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from parking.models import Booking, ParkingSlot
from django.conf import settings

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
    """Webhook endpoint for MPesa sandbox callbacks.
    In production, secure this endpoint (validate payload, use HTTPS, verify signatures).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))

        # Safaricom sandbox/Daraja formats vary: try to extract common fields from nested structures
        booking_id = None
        receipt = None
        status = None

        # Direct top-level keys
        if isinstance(payload, dict):
            booking_id = payload.get('booking_id') or payload.get('CheckoutRequestID') or payload.get('MerchantRequestID')
            receipt = payload.get('receipt') or payload.get('MpesaReceiptNumber')
            status = payload.get('status') or payload.get('ResultCode')

        # Common Daraja STK callback structure: { "Body": { "stkCallback": { ... }}}
        try:
            body = payload.get('Body') if isinstance(payload, dict) else None
            if body:
                stk = body.get('stkCallback') or body.get('stkcallback')
                if stk:
                    status = stk.get('ResultCode') or status
                    # MerchantRequestID / CheckoutRequestID may be present
                    booking_id = booking_id or stk.get('CheckoutRequestID') or stk.get('MerchantRequestID')
                    # Result parameters hold MpesaReceiptNumber
                    result = stk.get('CallbackMetadata') or stk.get('Callback') or {}
                    if isinstance(result, dict):
                        # CallbackMetadata has 'Item' list with Name/Value
                        items = result.get('Item') or result.get('Items') or []
                        for it in items:
                            name = it.get('Name') or it.get('name')
                            if name and name.lower() in ('mpesareceiptnumber', 'mpesareceiptnumber', 'mpesareceipt'):
                                receipt = it.get('Value') or receipt
        except Exception:
            # ignore nested parsing errors and fall back to top-level values
            pass

        # Validate optional callback secret
        secret = getattr(settings, 'MPESA_CALLBACK_SECRET', '')
        if secret:
            header_secret = request.headers.get('X-MPESA-CALLBACK-SECRET') or request.headers.get('X-Callback-Secret')
            if not header_secret or header_secret != secret:
                return JsonResponse({'error': 'forbidden'}, status=403)

        if not booking_id:
            return JsonResponse({'error': 'missing booking_id'}, status=400)

        booking = Booking.objects.get(pk=booking_id)

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

        booking.payment_status = Booking.STATUS_FAILED
        booking.save()
        return JsonResponse({'ok': False})

    except Booking.DoesNotExist:
        return JsonResponse({'error': 'booking not found'}, status=404)
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)
