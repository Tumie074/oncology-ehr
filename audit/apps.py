from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = 'audit'

    def ready(self):
        from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
        from .models import log

        user_logged_in.connect(lambda sender, request, user, **kw: log(request, 'USER_LOGIN', user=user), weak=False)
        user_logged_out.connect(lambda sender, request, user, **kw: log(request, 'USER_LOGOUT', user=user), weak=False)
        user_login_failed.connect(
            lambda sender, credentials, request=None, **kw: log(request, 'LOGIN_FAILED', credentials.get('username', ''), anonymous=True),
            weak=False)
