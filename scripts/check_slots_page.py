from django.test import Client

client = Client()
resp = client.get('/parking/slots/')
print('Status:', resp.status_code)
print('Title snippet:', resp.content[:400].decode('utf-8', errors='replace'))
