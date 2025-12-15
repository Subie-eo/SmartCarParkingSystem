import os, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API_KEY = os.getenv('SENDGRID_API_KEY')
if not API_KEY:
    # try loading from .env in project root
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    print('Looking for .env at', env_path)
    print('exists:', os.path.exists(env_path))
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            text = f.read()
            print('Full .env length:', len(text))
            if 'SENDGRID' in text:
                print('Found SENDGRID in .env')
                lines = text.splitlines()
                for i, raw_line in enumerate(lines):
                    if 'SENDGRID' in raw_line:
                        print('Context around SENDGRID line index', i)
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            print(j, repr(lines[j]))
                for raw_line in lines:
                    line = raw_line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"\'')
                        if k == 'SENDGRID_API_KEY':
                            API_KEY = v
                            print('Loaded SENDGRID_API_KEY from .env (length', len(API_KEY), ')')
                            print('repr:', repr(API_KEY))
                            # show hex codes for up to first 100 chars
                            print('hex:', ' '.join(hex(ord(c)) for c in API_KEY[:100]))
                            break
TO = os.getenv('TEST_EMAIL_RECIPIENT') or os.getenv('EMAIL_HOST_USER')
FROM = os.getenv('DEFAULT_FROM_EMAIL') or os.getenv('EMAIL_HOST_USER')

if not API_KEY:
    print('SENDGRID_API_KEY not set')
    raise SystemExit(1)
if not TO:
    print('No recipient configured')
    raise SystemExit(1)

payload = {
    'personalizations': [{'to': [{'email': TO}], 'subject': 'SendGrid API test'}],
    'from': {'email': FROM},
    'content': [{'type': 'text/plain', 'value': 'This is a SendGrid API test message.'}]
}

data = json.dumps(payload).encode('utf-8')
req = Request('https://api.sendgrid.com/v3/mail/send', data=data, method='POST')
req.add_header('Authorization', f'Bearer {API_KEY}')
req.add_header('Content-Type', 'application/json')

try:
    resp = urlopen(req, timeout=20)
    print('Status:', resp.getcode())
    body = resp.read().decode('utf-8')
    print('Body:', body)
except HTTPError as e:
    print('HTTPError:', e.code)
    try:
        print(e.read().decode('utf-8'))
    except Exception:
        pass
except URLError as e:
    print('URLError:', e.reason)
except Exception as e:
    print('Exception:', e)
