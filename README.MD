# CarParking

CarParking is a small Django-based parking reservation system designed for drivers and lot operators. It supports:

- Slot inventory management (admin)
- Driver booking flow with M-Pesa STK integration (simulated in development)
- Real-time occupancy tracking and dashboard statistics
- Email password reset using Django's built-in password reset views

## Quick start (development)

Prerequisites:

- Python 3.12
- pip

Install dependencies:

```bash
pip install -r requirements.txt
```

## CarParking

CarParking is a Django-based parking reservation system focused on drivers.
It supports booking, M-Pesa payments (STK Push), and a driver dashboard with
real-time availability.

This README covers local setup, environment variables, testing, and how to
switch from simulated M-Pesa behavior to real STK pushes.

### Prerequisites
- Python 3.12
- pip

### Quick setup (development)
1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Apply migrations and create a superuser:

```powershell
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py createsuperuser
```

4. Run the development server:

```powershell
.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

### Important URLs
- Home: `/`
- Login: `/accounts/login/`
- Register: `/accounts/register/`
- Driver Dashboard: `/accounts/driver_dashboard/` (after login)
- Admin slot management: `/parking/admin/slots/`

### Environment variables (important)
Create a `.env` file with the following (examples):

```
DEBUG=True
SECRET_KEY=your-dev-secret
MPESA_SIMULATE=True          # True => local simulation; False => real STK pushes
MPESA_CONSUMER_KEY=...
MPESA_CONSUMER_SECRET=...
MPESA_SHORTCODE=174379
MPESA_PASSKEY=...
MPESA_API_BASE=https://sandbox.safaricom.co.ke
MPESA_CALLBACK_URL=https://your-ngrok.ngrok.io/parking/payment/callback/

EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend
EMAIL_FILE_PATH=./sent_emails
```

Notes:
- `MPESA_SIMULATE=True` is the default for development — the app will schedule
    a local confirmation and will NOT send a real STK push.
- To run real STK pushes set `MPESA_SIMULATE=False` and provide valid
    Daraja credentials and a reachable `MPESA_CALLBACK_URL` (use ngrok for local testing).

### Testing & commands
- Run Django system checks:

```powershell
.venv\Scripts\python.exe manage.py check
```

- Run the app test suite (includes booking flow tests which exercise the simulated STK):

```powershell
.venv\Scripts\python.exe manage.py test -v2
```

- Send a test email using the management command (supports temporary SMTP overrides):

```powershell
.venv\Scripts\python.exe manage.py send_test_email --type test --email you@example.com \
    --smtp-host smtp.example.com --smtp-port 587 --smtp-user you --smtp-password 'pa$$' --smtp-use-tls --from-email noreply@yourdomain.com
```

### Switching to real M-Pesa STK pushes (WARNING)
To send real STK pushes to users' phones:

1. Set `MPESA_SIMULATE=False` in your `.env`.
2. Provide valid `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE`, and `MPESA_PASSKEY`.
3. Ensure `MPESA_CALLBACK_URL` is reachable by Safaricom (use ngrok for local testing and configure the sandbox).
4. Restart the server and monitor logs — failures and responses are logged by the M-Pesa client.

Be careful: a real STK push will prompt the target phone to approve a payment.

### Email delivery options
- Development (default): file-based backend writing to `sent_emails/`.
- Production: use SMTP or a provider such as SendGrid. See `CarParking/email_backends.py` for a minimal SendGrid backend.

### Useful maintenance
- Logs and debug files (e.g. `smtp_debug_output.log`) can be removed if they contain sensitive data — they are safe to delete.
- Keep `.env` private and do not commit it.

### Contributing
Please open issues or PRs. For major changes, open an issue first to discuss.

---

Last updated: December 2025
