from django.conf import settings
from .rbac import get_role, permissions_for


def chrs(request):
    user = request.user
    return {
        'chrs_role': get_role(user),
        'chrs_perms': permissions_for(user),
        'lock_seconds': settings.INACTIVITY_LOCK_SECONDS,
    }
