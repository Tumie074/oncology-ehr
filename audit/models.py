from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """Append-only record of who did what and when (POPIA accountability)."""
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=40)
    detail = models.CharField(max_length=300, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.timestamp:%Y-%m-%d %H:%M} {self.username} {self.action}'


def log(request, action, detail='', user=None, anonymous=False):
    user = user or getattr(request, 'user', None)
    authed = bool(user and getattr(user, 'is_authenticated', False)) and not anonymous
    ip = None
    if request is not None:
        fwd = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip = (fwd.split(',')[0].strip() if fwd else request.META.get('REMOTE_ADDR')) or None
    AuditEvent.objects.create(
        user=user if authed else None,
        username=user.get_username() if authed else (detail if anonymous else ''),
        action=action,
        detail='' if anonymous else detail[:300],
        ip_address=ip,
    )
