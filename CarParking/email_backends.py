import os
import json
import time
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class SendGridBackend(BaseEmailBackend):
    """Minimal SendGrid HTTP backend.

    Usage: set `EMAIL_BACKEND = 'CarParking.email_backends.SendGridBackend'`
    and provide `SENDGRID_API_KEY` in the environment.
    This is a lightweight fallback for environments where SMTP is blocked.
    """

    SENDGRID_URL = 'https://api.sendgrid.com/v3/mail/send'

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = os.getenv('SENDGRID_API_KEY')
        if not api_key:
            raise RuntimeError('SENDGRID_API_KEY not set')

        sent = 0
        for message in email_messages:
            if not isinstance(message, EmailMessage):
                continue
            payload = {
                'personalizations': [
                    {
                        'to': [{'email': addr} for addr in message.to or []],
                        'subject': message.subject,
                    }
                ],
                'from': {'email': message.from_email},
                'content': [
                    {'type': 'text/plain', 'value': message.body}
                ]
            }

            data = json.dumps(payload).encode('utf-8')
            req = Request(self.SENDGRID_URL, data=data, method='POST')
            req.add_header('Authorization', f'Bearer {api_key}')
            req.add_header('Content-Type', 'application/json')

            try:
                resp = urlopen(req, timeout=20)
                code = resp.getcode()
                if 200 <= code < 300:
                    sent += 1
            except HTTPError as e:
                # If SendGrid rejects due to unverified sender, fallback to file backend
                try:
                    body = e.read().decode('utf-8')
                except Exception:
                    body = str(e)
                # Detect common SendGrid sender identity error
                if e.code == 403 and ('Sender Identity' in body or 'from address' in body.lower() or 'verified' in body.lower()):
                    # Ensure email file path exists
                    file_dir = getattr(settings, 'EMAIL_FILE_PATH', None) or (settings.BASE_DIR / 'sent_emails')
                    file_dir = str(file_dir)
                    try:
                        os.makedirs(file_dir, exist_ok=True)
                    except Exception:
                        pass

                    timestamp = int(time.time() * 1000)
                    safe_name = f"sendgrid-fallback-{timestamp}.log"
                    file_path = os.path.join(file_dir, safe_name)
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f"Subject: {message.subject}\n")
                            f.write(f"From: {message.from_email}\n")
                            f.write(f"To: {', '.join(message.to or [])}\n\n")
                            f.write(str(message.body))
                        sent += 1
                    except Exception:
                        # If writing fails, re-raise original error so caller sees failure
                        raise
                else:
                    raise
            except URLError:
                raise

        return sent
