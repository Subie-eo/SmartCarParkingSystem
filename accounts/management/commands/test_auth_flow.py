from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Test registration and login flow using the Django test client (with CSRF checks)'

    def handle(self, *args, **options):
        User = get_user_model()
        client = Client(enforce_csrf_checks=True)

        # 1) GET registration page to obtain CSRF token
        resp = client.get('/accounts/register/')
        print('GET /accounts/register/ status:', resp.status_code)
        csrftoken = client.cookies.get('csrftoken')
        if not csrftoken:
            print('No csrftoken cookie set on GET')
        else:
            token = csrftoken.value
            print('csrftoken obtained')

        # Prepare registration data
        email = 'flowtester@example.com'
        username = 'flowtester'
        password = 'FlowPass123'
        phone = '0712345679'
        plate = 'FLOW123'
        data = {
            'csrfmiddlewaretoken': token if csrftoken else '',
            'username': username,
            'email': email,
            'phone_number': phone,
            'vehicle_plate': plate,
            'vehicle_type': 'sedan',
            'password1': password,
            'password2': password,
        }

        # POST registration
        resp = client.post('/accounts/register/', data, follow=True)
        print('POST /accounts/register/ status:', resp.status_code)
        # Check if user created
        created = User.objects.filter(email=email).exists()
        print('User created?', created)

        # If created, attempt login
        if created:
            # GET login page to obtain fresh CSRF
            resp = client.get('/accounts/login/')
            csrftoken = client.cookies.get('csrftoken')
            token = csrftoken.value if csrftoken else ''
            login_data = {
                'csrfmiddlewaretoken': token,
                'username': email,
                'password': password,
            }
            resp = client.post('/accounts/login/', login_data, follow=True)
            print('POST /accounts/login/ status:', resp.status_code)
            # Check if authenticated by inspecting context user
            # The test client stores session; check session _auth_user_id
            session = client.session
            auth_user_id = session.get('_auth_user_id')
            print('Authenticated user id in session:', auth_user_id)

            # Clean up created user
            User.objects.filter(email=email).delete()
            print('Cleaned up test user')
        else:
            print('Registration failed; skipping login test')
