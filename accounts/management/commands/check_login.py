from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model, authenticate

class Command(BaseCommand):
    help = 'Create a temp user and test authentication'

    def handle(self, *args, **options):
        User = get_user_model()
        email = 'testuser@example.com'
        password = 'TestPass123'
        # Remove any existing test user
        User.objects.filter(email=email).delete()
        print('Creating user', email)
        user = User.objects.create_user(
            email=email,
            username='testuser',
            phone_number='0712345678',
            vehicle_plate='TEST123',
            password=password
        )
        print('User created:', user.pk)
        # Try to authenticate using username=email (since USERNAME_FIELD='email')
        usr = authenticate(username=email, password=password)
        print('authenticate(username=email):', bool(usr))
        # Also try authenticate with email kw (some backends might use it)
        try:
            usr2 = authenticate(email=email, password=password)
            print('authenticate(email=email):', bool(usr2))
        except Exception as e:
            print('authenticate(email=...) raised:', e)
        # Check stored password hash
        print('check_password:', user.check_password(password))
        # Clean up
        User.objects.filter(email=email).delete()
        print('Done')
