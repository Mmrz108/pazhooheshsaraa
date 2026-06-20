from urllib.parse import quote

from django.conf import settings
from django.shortcuts import redirect

from common.admin_session import admin_session_allowed


class AdminAccessMiddleware:
    """Restrict Django admin to staff who passed the site-management password gate."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if path == '/admin/login/':
            return redirect(settings.ADMIN_ACCESS_LOGIN_URL)

        if path.startswith('/admin/'):
            if self._is_public_admin_path(path):
                return self.get_response(request)

            if not admin_session_allowed(request):
                login_url = settings.ADMIN_ACCESS_LOGIN_URL
                next_path = quote(request.get_full_path())
                return redirect(f'{login_url}?next={next_path}')

        return self.get_response(request)

    @staticmethod
    def _is_public_admin_path(path):
        return (
            path.startswith('/admin/static/')
            or path == '/admin/jsi18n/'
        )
