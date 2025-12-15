from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.conf import settings
import socket

class Command(BaseCommand):
    help = 'Send a test email or a password-reset email to validate email configuration.'

    def add_arguments(self, parser):
        parser.add_argument('--email', '-e', dest='email', help='Target email address', required=False)
        parser.add_argument('--type', '-t', dest='type', choices=['test', 'reset'], default='test', help='Type: "test" sends a simple message; "reset" sends a password reset link')
        # Optional SMTP overrides for one-off tests without changing env
        parser.add_argument('--smtp-host', dest='smtp_host', help='SMTP host to use for this test', required=False)
        parser.add_argument('--smtp-port', dest='smtp_port', type=int, help='SMTP port', required=False)
        parser.add_argument('--smtp-user', dest='smtp_user', help='SMTP username', required=False)
        parser.add_argument('--smtp-password', dest='smtp_password', help='SMTP password', required=False)
        parser.add_argument('--smtp-use-tls', dest='smtp_use_tls', action='store_true', help='Use TLS for SMTP', required=False)
        parser.add_argument('--from-email', dest='from_email', help='Override FROM address for this test', required=False)

    def handle(self, *args, **options):
        email = options.get('email')
        email_type = options.get('type')

        User = get_user_model()

        # Determine a default target if none provided (first user)
        if not email:
            try:
                user = User.objects.filter(email__isnull=False).first()
                if not user:
                    raise CommandError('No users with email found; please provide an --email target.')
                email = user.email
                self.stdout.write(self.style.NOTICE(f'No --email specified, using first user: {email}'))
            except Exception as exc:
                raise CommandError(f'Failed to determine default user: {exc}')

        # If SMTP overrides were provided, temporarily apply them to settings
        smtp_host = options.get('smtp_host')
        smtp_port = options.get('smtp_port')
        smtp_user = options.get('smtp_user')
        smtp_password = options.get('smtp_password')
        smtp_use_tls = options.get('smtp_use_tls')
        from_email_override = options.get('from_email')

        if smtp_host:
            # apply ephemeral SMTP config for this command
            settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
            settings.EMAIL_HOST = smtp_host
            if smtp_port:
                settings.EMAIL_PORT = smtp_port
            settings.EMAIL_HOST_USER = smtp_user or ''
            settings.EMAIL_HOST_PASSWORD = smtp_password or ''
            settings.EMAIL_USE_TLS = bool(smtp_use_tls)
            if from_email_override:
                settings.DEFAULT_FROM_EMAIL = from_email_override

        # Validate backend by sending a simple message or a reset
        # If using SMTP backend, try a quick connectivity/auth check so failures are surfaced early
        if 'smtp' in getattr(settings, 'EMAIL_BACKEND', ''):
            try:
                host = getattr(settings, 'EMAIL_HOST', 'localhost')
                port = int(getattr(settings, 'EMAIL_PORT', 25))
                use_tls = bool(getattr(settings, 'EMAIL_USE_TLS', False))
                user = getattr(settings, 'EMAIL_HOST_USER', '')
                pwd = getattr(settings, 'EMAIL_HOST_PASSWORD', '')

                self.stdout.write(self.style.NOTICE(f'Testing SMTP connection to {host}:{port} (TLS={use_tls})'))
                # Use a short timeout for quick feedback
                sock = socket.create_connection((host, port), timeout=10)
                sock.close()

                # If authentication info is provided, attempt to login via smtplib to validate credentials
                if user and pwd:
                    import smtplib
                    try:
                        server = smtplib.SMTP(host, port, timeout=10)
                        if use_tls:
                            server.starttls()
                        server.login(user, pwd)
                        server.quit()
                    except smtplib.SMTPAuthenticationError as exc:
                        raise CommandError(f'SMTP authentication failed: {exc}')
                    except Exception as exc:
                        # Non-auth errors (e.g., TLS negotiation) will be raised below when sending
                        self.stdout.write(self.style.WARNING(f'SMTP connectivity check warning: {exc}'))
            except socket.timeout:
                raise CommandError('Timed out connecting to SMTP server. Check EMAIL_HOST and EMAIL_PORT and network connectivity.')
            except Exception as exc:
                raise CommandError(f'Failed to validate SMTP connectivity: {exc}')

        if email_type == 'test':
            from django.conf import settings as _settings
            site = getattr(_settings, 'SITE_NAME', 'SmartPark')
            subject = f'{site}: test email'
            body = f'This is a test email from {site}. If you received this, your email settings are working.'
            try:
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
                self.stdout.write(self.style.SUCCESS(f'Test email sent to {email}'))
            except BadHeaderError:
                raise CommandError('Invalid header found')
            except Exception as exc:
                raise CommandError(f'Failed to send test email: {exc}')

        else:  # reset
            # Use PasswordResetForm to generate the same email content and sending logic used by the site
            form = PasswordResetForm({'email': email})
            if not form.is_valid():
                raise CommandError('PasswordResetForm invalid for provided email (no active user with that email).')
            try:
                # domain_override ensures the reset link is generated for localhost if needed
                # PasswordResetForm.save() uses Django settings for email sending; if the caller provided
                # SMTP overrides via options we already applied them to `settings` above.
                form.save(domain_override='localhost:8000', use_https=False, from_email=getattr(settings,'DEFAULT_FROM_EMAIL', None))
                self.stdout.write(self.style.SUCCESS(f'Password reset email dispatched to {email}. Check your configured email backend (console, file, or SMTP).'))
            except Exception as exc:
                raise CommandError(f'Failed to send password reset email: {exc}')
