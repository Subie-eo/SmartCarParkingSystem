from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'List superusers or reset a superuser password. Use --list to show superusers. Use --email and --password to set.'

    def add_arguments(self, parser):
        parser.add_argument('--list', action='store_true', help='List all superusers')
        parser.add_argument('--email', help='Email of superuser to change password for')
        parser.add_argument('--username', help='Username of superuser to change password for')
        parser.add_argument('--password', help='New password to set')

    def handle(self, *args, **options):
        User = get_user_model()
        if options.get('list'):
            su = User.objects.filter(is_superuser=True)
            if not su.exists():
                self.stdout.write('No superusers found.')
                return
            self.stdout.write('Superusers:')
            for u in su:
                self.stdout.write(f'- pk={u.pk} email={u.email} username={u.username} is_active={u.is_active}')
            return

        email = options.get('email')
        username = options.get('username')
        password = options.get('password')

        if not password:
            self.stderr.write('Error: --password is required to set a new password')
            return

        qs = User.objects.none()
        if email:
            qs = User.objects.filter(email__iexact=email, is_superuser=True)
        elif username:
            qs = User.objects.filter(username__iexact=username, is_superuser=True)
        else:
            su = User.objects.filter(is_superuser=True)
            if su.count() == 1:
                qs = su
            else:
                self.stderr.write('Multiple superusers exist; specify --email or --username to select which one to reset.')
                return

        if not qs.exists():
            self.stderr.write('No matching superuser found.')
            return

        user = qs.first()
        user.set_password(password)
        user.save()
        self.stdout.write(f'Success: password for superuser (pk={user.pk} email={user.email} username={user.username}) has been updated')
