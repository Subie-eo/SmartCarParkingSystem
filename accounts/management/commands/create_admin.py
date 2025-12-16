from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a superuser with required fields (email, username, phone, vehicle_plate, password)'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Email for the admin user')
        parser.add_argument('--username', required=True, help='Username for the admin user')
        parser.add_argument('--password', required=True, help='Password for the admin user')
        parser.add_argument('--phone', required=False, help='Phone number (required by custom user model)')
        parser.add_argument('--plate', required=False, help='Vehicle plate (required by custom user model)')

    def handle(self, *args, **options):
        User = get_user_model()
        email = options['email']
        username = options['username']
        password = options['password']
        phone = options.get('phone') or '0790000001'
        plate = options.get('plate') or 'ADMIN001'

        # Check for existing user with same email
        if User.objects.filter(email__iexact=email).exists():
            self.stderr.write(f'User with email {email} already exists. Aborting.')
            return

        try:
            user = User.objects.create_superuser(
                email=email,
                username=username,
                phone_number=phone,
                vehicle_plate=plate,
                password=password
            )
            self.stdout.write(f'Success: created superuser pk={user.pk} email={user.email} username={user.username}')
        except Exception as e:
            self.stderr.write(f'Error creating superuser: {e}')
