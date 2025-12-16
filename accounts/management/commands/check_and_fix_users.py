from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Report user account issues and optionally apply safe fixes (lowercase emails, fill missing usernames)'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='Apply safe fixes')

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.all().order_by('pk')
        if not users.exists():
            self.stdout.write('No users found.')
            return

        report = []
        for u in users:
            issues = []
            email = getattr(u, 'email', '') or ''
            username = getattr(u, 'username', '') or ''
            if email != email.lower():
                issues.append('email-not-lower')
            if not username:
                issues.append('missing-username')
            if not u.has_usable_password():
                issues.append('no-usable-password')
            if not u.is_active:
                issues.append('inactive')
            report.append((u.pk, email, username, issues))

        # Print report
        self.stdout.write('Found %d users\n' % users.count())
        for pk, email, username, issues in report:
            self.stdout.write('- pk=%s email=%s username=%s issues=%s' % (pk, email, username, ','.join(issues) if issues else 'OK'))

        # Apply safe fixes if requested
        if options.get('fix'):
            self.stdout.write('\nApplying safe fixes: lowercase emails and fill missing usernames')
            changed = 0
            for pk, email, username, issues in report:
                u = User.objects.get(pk=pk)
                modified = False
                if 'email-not-lower' in issues:
                    u.email = email.lower()
                    modified = True
                if 'missing-username' in issues and u.email:
                    # derive username from email local-part
                    local = u.email.split('@')[0]
                    # ensure uniqueness by appending pk if needed
                    candidate = local
                    qs = User.objects.filter(username=candidate).exclude(pk=u.pk)
                    if qs.exists():
                        candidate = f"{local}{u.pk}"
                    u.username = candidate
                    modified = True
                if modified:
                    u.save()
                    changed += 1
                    self.stdout.write('Fixed user pk=%s (now username=%s email=%s)' % (u.pk, u.username, u.email))
            self.stdout.write('\nCompleted fixes. %d user(s) updated.' % changed)
        else:
            self.stdout.write('\nRun with --fix to apply safe fixes (lowercase emails, fill missing usernames).')
