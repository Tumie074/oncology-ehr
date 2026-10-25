"""Role-based access control mirroring the CHRS role/permission matrix.

Roles are Django Groups (Admin, Physician, Nurse, Counselor). Superusers are Admins (and may use /admin/ to manage users).
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login

ROLES = ['Admin', 'Physician', 'Nurse', 'Counselor']

# Matches the CHRS role matrix (src/utils/rbac.ts): the Camp Administrator has no clinical
# editing rights; the Physician owns audit logs and incident reports with the Nurse.
ROLE_PERMISSIONS = {
    'Admin': {'VIEW_CLINICAL_RECORDS', 'MANAGE_USERS', 'IMPORT_CSV'},
    'Physician': {'VIEW_CLINICAL_RECORDS', 'EDIT_CLINICAL_RECORDS', 'IMPORT_CSV', 'VIEW_AUDIT_LOGS', 'FILE_INCIDENT_REPORT'},
    'Nurse': {'VIEW_CLINICAL_RECORDS', 'EDIT_CLINICAL_RECORDS', 'FILE_INCIDENT_REPORT'},
    'Counselor': {'VIEW_CLINICAL_RECORDS'},
}


def get_role(user):
    if not getattr(user, 'is_authenticated', False):
        return None
    if user.is_superuser:
        return 'Admin'
    names = set(user.groups.values_list('name', flat=True))
    for role in ROLES:  # highest privilege first
        if role in names:
            return role
    return None


def permissions_for(user):
    return ROLE_PERMISSIONS.get(get_role(user), set())


def has_permission(user, permission):
    return permission in permissions_for(user)


def permission_required(permission):
    """View decorator: login required, then the role must hold `permission`."""
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not has_permission(request.user, permission):
                from audit.models import log
                log(request, 'ACCESS_DENIED', f'{permission} on {request.path}')
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
