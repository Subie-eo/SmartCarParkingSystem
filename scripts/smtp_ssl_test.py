import os, sys, traceback
import smtplib
from email.message import EmailMessage

# Load .env if present
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
PORT = int(os.getenv('EMAIL_PORT', '465'))
USER = os.getenv('EMAIL_HOST_USER')
PWD = os.getenv('EMAIL_HOST_PASSWORD')
FROM = os.getenv('DEFAULT_FROM_EMAIL') or USER
TO = os.getenv('TEST_EMAIL_RECIPIENT') or USER

logfile = os.path.join(os.path.dirname(__file__), '..', 'smtp_ssl_test.log')

def log(msg):
    try:
        with open(logfile, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except Exception:
        pass
    print(msg)

log('--- SMTP SSL Test start ---')
log(f'HOST={HOST} PORT={PORT} USER={USER} FROM={FROM} TO={TO}')

if not HOST:
    log('No EMAIL_HOST set; aborting')
    sys.exit(1)

try:
    log('Attempting SMTP_SSL connection...')
    server = smtplib.SMTP_SSL(HOST, PORT, timeout=30)
    server.set_debuglevel(1)
    try:
        code, msg = server.ehlo()
        log(f'EHLO: {code} {msg}')
    except Exception as e:
        log('EHLO failed: ' + repr(e))

    if USER and PWD:
        try:
            log('Attempting LOGIN...')
            server.login(USER, PWD)
            log('Login successful')
        except Exception as e:
            log('Login failed: ' + repr(e))

    msg = EmailMessage()
    msg['Subject'] = 'SMTP SSL debug test'
    msg['From'] = FROM
    msg['To'] = TO
    msg.set_content('This is a smtp_ssl_test.py debug message')
    try:
        res = server.send_message(msg)
        log('send_message result: ' + repr(res))
    except Exception as e:
        log('send_message failed: ' + repr(e))

    try:
        server.quit()
        log('SMTP_SSL session ended')
    except Exception as e:
        log('Error quitting SMTP_SSL: ' + repr(e))
except Exception:
    tb = traceback.format_exc()
    log('SMTP_SSL connection failed:')
    log(tb)
    sys.exit(1)

log('--- SMTP SSL Test end ---')
