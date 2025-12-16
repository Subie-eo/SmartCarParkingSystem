from django.core.management.base import BaseCommand
from django.test import Client
from django.conf import settings

class Command(BaseCommand):
    help = 'Login as admin and GET /parking/admin/slots/ then attempt to create a slot to verify admin flows.'

    def add_arguments(self, parser):
        parser.add_argument('--email', help='Admin email', default='scpadmin@gmail.com')
        parser.add_argument('--password', help='Admin password', default='Elias3128')
        parser.add_argument('--slot_id', help='Slot id to create', default='Z-999')
        parser.add_argument('--slot_name', help='Slot name', default='Admin Created Slot')
        parser.add_argument('--level', help='Slot level', default='Admin')
        parser.add_argument('--pricing', help='Pricing category', default='Regular')

    def handle(self, *args, **options):
        c = Client()
        email = options['email']
        password = options['password']
        logged = c.login(username=email, password=password)
        self.stdout.write(f'Login successful: {logged}')

        resp = c.get('/parking/admin/slots/')
        self.stdout.write(f'GET /parking/admin/slots/ status: {resp.status_code}')
        if resp.status_code != 200:
            self.stdout.write('Cannot access admin slot list; ensure user is staff/superuser and credentials are correct')
            return

        # Prepare form data for ParkingSlotForm
        data = {
            'slot_id': options['slot_id'],
            'slot_name': options['slot_name'],
            'level': options['level'],
            'pricing_category': options['pricing'],
            # unchecked checkbox field must be absent for False; include 'is_occupied' for True
            # keep it unchecked (False) by not including it
        }

        post = c.post('/parking/admin/slots/', data, follow=True)
        self.stdout.write(f'POST create slot status: {post.status_code}')
        if post.status_code == 200 or post.status_code == 302:
            self.stdout.write('Slot creation attempted; checking listing...')
            list_resp = c.get('/parking/admin/slots/')
            text = list_resp.content.decode('utf-8', errors='replace')
            if options['slot_id'] in text:
                self.stdout.write(f'Success: slot {options["slot_id"]} found in admin listing')
            else:
                self.stdout.write(f'Create attempt completed but slot {options["slot_id"]} not present in listing (maybe duplicate or validation error).')
        else:
            self.stdout.write('Failed to POST create slot; status code: %s' % post.status_code)
