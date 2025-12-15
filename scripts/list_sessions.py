from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model

User = get_user_model()

sessions = Session.objects.all()
print("Total sessions:", sessions.count())
print("---")
for s in sessions:
    try:
        data = s.get_decoded()
    except Exception as e:
        print("Failed to decode session", s.session_key, e)
        continue
    uid = data.get('_auth_user_id')
    user_info = None
    if uid:
        try:
            u = User.objects.get(pk=uid)
            user_info = f"{u.pk} {getattr(u, 'email', None) or getattr(u, 'username', None)}"
        except User.DoesNotExist:
            user_info = f"{uid} (no matching user)"
    print(f"SESSION_KEY={s.session_key} UID={uid} USER={user_info} EXPIRES={s.expire_date}")
