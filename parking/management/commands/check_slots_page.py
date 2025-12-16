from django.core.management.base import BaseCommand
from django.test import Client

class Command(BaseCommand):
    help = 'GET /parking/slots/ using test client and print status and snippet'

    def handle(self, *args, **options):
        c = Client()
        r = c.get('/parking/slots/')
        self.stdout.write(f'Status: {r.status_code}')
        text = r.content[:800].decode('utf-8', errors='replace')
        for line in text.splitlines()[:40]:
            self.stdout.write(line)
