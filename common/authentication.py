from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class LenientJWTAuthentication(JWTAuthentication):
    """Treat invalid/expired Bearer tokens as anonymous instead of returning 401."""

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None
        try:
            return super().authenticate(request)
        except AuthenticationFailed:
            return None
