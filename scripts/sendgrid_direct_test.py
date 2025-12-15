import os, re, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Read .env and extract SENDGRID_API_KEY
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
key = None
with open(env_path, encoding='utf-8') as f:
    for line in f:
        m = re.match(r'^\s*SENDGRID_API_KEY\s*=\s*(.*)\s*$', line)
        if m:
            val = m.group(1).strip().strip('"\'')
            if val:
                key = val
            else:
                key = ''
            break

if key is None:
    print('SENDGRID_API_KEY not found in .env')
    raise SystemExit(1)
if key == '':
    print('SENDGRID_API_KEY is empty in .env')
    raise SystemExit(1)

TO = os.getenv('TEST_EMAIL_RECIPIENT') or 'eliasombonya@gmail.com'
FROM = os.getenv('DEFAULT_FROM_EMAIL') or os.getenv('EMAIL_HOST_USER') or TO

payload = {
    'personalizations': [{'to': [{'email': TO}], 'subject': 'SendGrid API test (direct)'}],
    'from': {'email': FROM},
    'content': [{'type': 'text/plain', 'value': 'This is a direct SendGrid API test message.'}]
}

data = json.dumps(payload).encode('utf-8')
req = Request('https://api.sendgrid.com/v3/mail/send', data=data, method='POST')
req.add_header('Authorization', f'Bearer {key}')
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
