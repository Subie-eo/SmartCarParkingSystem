#!/usr/bin/env python3
import os, sys
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CarParking.settings')
import django
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    user = User.objects.get(username='sub')
except Exception as e:
    print('User not found', e)
    sys.exit(1)

c = Client()
# login using email and password? We don't know password; use force_login
c.force_login(user)
resp = c.get('/parking/slots/', HTTP_HOST='127.0.0.1')
print('Status code:', resp.status_code)
print('Template used:', [t.name for t in resp.templates])
print('Context available:', resp.context is not None)
content = resp.content.decode('utf-8')
start = content.find('Current Status:')
if start != -1:
    snippet = content[start:start+400]
    print('Found status snippet:\n', snippet)
else:
    print('Status text not found in response body (first 2000 chars):')
    print(content[:2000])
