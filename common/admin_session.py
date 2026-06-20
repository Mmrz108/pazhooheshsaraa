"""Django session helpers for gated admin access."""

from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout

ADMIN_ACCESS_VERIFIED_KEY = 'admin_access_verified'
ADMIN_ACCESS_USER_ID_KEY = 'admin_access_user_id'


def clear_admin_session(request) -> None:
    """Remove any Django login and admin gate flags from the session."""
    django_logout(request)
    request.session.pop(ADMIN_ACCESS_VERIFIED_KEY, None)
    request.session.pop(ADMIN_ACCESS_USER_ID_KEY, None)


def grant_admin_session(request, user) -> None:
    """Create a fresh staff session after the admin password gate."""
    clear_admin_session(request)
    django_login(request, user)
    request.session[ADMIN_ACCESS_VERIFIED_KEY] = True
    request.session[ADMIN_ACCESS_USER_ID_KEY] = user.pk
    request.session.modified = True


def admin_session_allowed(request) -> bool:
    user = request.user
    if not user.is_authenticated or not user.is_staff:
        return False
    if not request.session.get(ADMIN_ACCESS_VERIFIED_KEY):
        return False
    return request.session.get(ADMIN_ACCESS_USER_ID_KEY) == user.pk
