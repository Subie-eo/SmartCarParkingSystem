import os
import smtplib
from email.message import EmailMessage
import traceback
import sys
# Try to load .env if values are not in the environment
ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
if not os.getenv('EMAIL_HOST') and os.path.exists(ENV_PATH):
    try:
        with open(ENV_PATH, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    v = v.strip().strip('"\'')
                    if k and not os.getenv(k):
                        os.environ[k] = v
    except Exception:
        pass

HOST = os.getenv('EMAIL_HOST')
PORT = int(os.getenv('EMAIL_PORT', '587'))
USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('1','true','yes')
USER = os.getenv('EMAIL_HOST_USER')
PWD = os.getenv('EMAIL_HOST_PASSWORD')
FROM = os.getenv('DEFAULT_FROM_EMAIL') or USER
TO = os.getenv('TEST_EMAIL_RECIPIENT') or USER

print('SMTP debug')
print('HOST', HOST)
print('PORT', PORT)
print('USE_TLS', USE_TLS)
print('USER', USER)
print('FROM', FROM)
print('TO', TO)

if not HOST:
    print('No EMAIL_HOST set; aborting')
    raise SystemExit(1)

log_path = os.path.join(os.path.dirname(__file__), '..', 'smtp_debug_output.log')
def log(s):
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(s + '\n')
    except Exception:
        pass
    print(s)

try:
    log('Connecting to SMTP server...')
    server = smtplib.SMTP(HOST, PORT, timeout=30)
    server.set_debuglevel(1)
    log('Calling ehlo()')
    try:
        code, msg = server.ehlo()
        log(f'EHLO: {code} {msg}')
    except Exception as e:
        log('EHLO failed: ' + repr(e))

    if USE_TLS:
        log('Attempting STARTTLS...')
        try:
            server.starttls()
            code, msg = server.ehlo()
            log(f'EHLO after STARTTLS: {code} {msg}')
        except Exception as e:
            log('STARTTLS failed: ' + repr(e))

    if USER and PWD:
        try:
            log('Attempting LOGIN...')
            server.login(USER, PWD)
            log('Login successful')
        except Exception as e:
            log('Login failed: ' + repr(e))

    # Try to send a minimal message
    msg = EmailMessage()
    msg['Subject'] = 'SMTP debug test'
    msg['From'] = FROM
    msg['To'] = TO
    msg.set_content('This is a debug test message from smtp_debug.py')
    try:
        res = server.send_message(msg)
        log('send_message result: ' + repr(res))
    except Exception as e:
        log('send_message failed: ' + repr(e))

    try:
        server.quit()
        log('SMTP session ended')
    except Exception as e:
        log('Error quitting SMTP: ' + repr(e))
except Exception:
    tb = traceback.format_exc()
    log('SMTP connection failed with exception:')
    log(tb)
    sys.exit(1)
