import base64
import uuid
import threading
import time
import requests
from django.conf import settings
from django.utils import timezone
import logging
import re

from parking.models import Booking


class MpesaClient:
        """Mpesa client that supports Safaricom Daraja OAuth and STK Push.

        Behavior summary:
        - Reads credentials from Django `settings` (typically via `.env`).
        - When `MPESA_SIMULATE=True` the client schedules a small background task
            that marks a booking PAID after a delay; no external HTTP calls are made.
        - When `MPESA_SIMULATE=False` the client performs OAuth against the
            Daraja sandbox/production endpoint and posts an STK push request. All
            outgoing requests and responses are logged for easier debugging.

        Notes:
        - Phone numbers are normalized to the `2547XXXXXXXX` format by
            `_normalize_phone()` before being sent to Safaricom.
        - The client attempts to save `checkout_request_id` to the Booking record
            (best-effort) so the UI and webhooks can correlate results.
        """
    def __init__(self):
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.shortcode = getattr(settings, 'MPESA_SHORTCODE', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.simulate = getattr(settings, 'MPESA_SIMULATE', True)
        self.api_base = getattr(settings, 'MPESA_API_BASE', 'https://sandbox.safaricom.co.ke')
        self.callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')

        # Token cache
        self._token = None
        self._token_expiry = 0

    def _get_oauth_token(self) -> str:
        # Return cached token when valid
        if self._token and time.time() < self._token_expiry - 10:
            return self._token

        url = f"{self.api_base}/oauth/v1/generate?grant_type=client_credentials"
        try:
            resp = requests.get(url, auth=(self.consumer_key, self.consumer_secret), timeout=10)
            resp.raise_for_status()
            data = resp.json()
            token = data.get('access_token')
            expires_in = int(data.get('expires_in', 0))
            self._token = token
            self._token_expiry = time.time() + expires_in
            return token
        except Exception as e:
            logging.exception('Failed to fetch M-Pesa OAuth token from %s', url)
            raise

    def _build_password(self, timestamp: str) -> str:
        raw = f"{self.shortcode}{self.passkey}{timestamp}"
        return base64.b64encode(raw.encode('utf-8')).decode('utf-8')

    def _normalize_phone(self, phone: str) -> str:
        """Normalize common phone formats to Daraja expected format: 2547XXXXXXXX
        Accepts: 07XXXXXXXX, +2547XXXXXXXX, 7XXXXXXXX and returns '2547XXXXXXXX'.
        Raises ValueError on unsupported formats.
        """
        if not phone or not isinstance(phone, str):
            raise ValueError('Phone number required')
        p = re.sub(r"\D", "", phone)
        # Leading 0 (07xxxxxxxx)
        if len(p) == 10 and p.startswith('0'):
            return '254' + p[1:]
        # Leading 7 (7xxxxxxxx)
        if len(p) == 9 and p.startswith('7'):
            return '254' + p
        # Already in 2547... or 2541... form
        if p.startswith('254') and len(p) >= 12:
            return p
        # Leading plus
        if phone.startswith('+') and phone[1:].startswith('254'):
            return phone[1:]
        raise ValueError(f'Invalid phone number format for M-Pesa: {phone}')

    def stk_push(self, phone_number: str, amount: float, booking_id: int) -> str:
        """Initiate an STK push and return the CheckoutRequestID from Safaricom.

        phone_number must be in format 2547XXXXXXXX (no plus sign).
        """
        # Simulate locally if requested
        checkout_request_id = f"STK_{booking_id}_{uuid.uuid4().hex[:8]}"

        # timestamp format required by Daraja
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')

        if self.simulate:
            # schedule a local confirmation so the UI flow can be tested
            def _confirm():
                try:
                    b = Booking.objects.get(pk=booking_id)
                    b.payment_status = Booking.STATUS_PAID
                    b.mpesa_receipt_no = f"SIM-{booking_id}-{int(time.time())}"
                    if not b.end_time:
                        b.end_time = timezone.now() + timezone.timedelta(hours=1)
                    b.save()
                    slot = b.slot
                    slot.is_occupied = True
                    slot.save()
                except Exception:
                    pass

            t = threading.Timer(5.0, _confirm)
            t.daemon = True
            t.start()

            logging.info('MPESA simulate mode active: scheduled simulated confirmation for booking %s', booking_id)
            return checkout_request_id

        # Real STK Push path
        # Real STK Push path
        token = self._get_oauth_token()
        url = f"{self.api_base.rstrip('/')}/mpesa/stkpush/v1/processrequest"
        password = self._build_password(timestamp)

        # normalize phone numbers to expected Daraja format
        try:
            norm_phone = self._normalize_phone(phone_number)
        except Exception:
            logging.exception('Invalid phone number for booking %s: %s', booking_id, phone_number)
            raise

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": norm_phone,
            "PartyB": self.shortcode,
            "PhoneNumber": norm_phone,
            "CallBackURL": self.callback_url,
            "AccountReference": f"Booking{booking_id}",
            "TransactionDesc": f"Parking booking {booking_id}",
        }

        headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json'
        }

        try:
            logging.info('Sending STK push to %s (booking %s) via %s', norm_phone, booking_id, url)
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            logging.info('STK push response: %s', data)
        except Exception:
            logging.exception('STK push request failed to %s with payload %s', url, payload)
            raise

        # Expected keys: 'ResponseCode','ResponseDescription','CheckoutRequestID' in Daraja
        checkout_request_id = data.get('CheckoutRequestID') or data.get('MerchantRequestID') or checkout_request_id

        # Save to booking asynchronously (best-effort)
        try:
            b = Booking.objects.get(pk=booking_id)
            b.checkout_request_id = checkout_request_id
            b.save()
        except Exception:
            logging.exception('Failed to save checkout_request_id to Booking %s', booking_id)

        return checkout_request_id


def get_client():
    return MpesaClient()
