import mimetypes
import re

from django.conf import settings
from django.http import FileResponse, Http404
from django.views import View

CATEGORY_PAGE_PATTERN = re.compile(r'^courses/([^/]+)/?$')
COURSE_DETAIL_PATTERN = re.compile(r'^course/([^/]+)/?$')
ARTICLE_DETAIL_PATTERN = re.compile(r'^articles/([^/]+)/?$')
DEDICATED_PAGES = {
    'login': 'login-redirect.html',
    'login.html': 'login-redirect.html',
    'otp': 'login-redirect.html',
    'otp.html': 'login-redirect.html',
    'register': 'login-redirect.html',
    'register.html': 'login-redirect.html',
    'dashboard': 'dashboard.html',
    'dashboard.html': 'dashboard.html',
    'site-management': 'site-management.html',
    'site-management.html': 'site-management.html',
}


class FrontendView(View):
    """Serve the frontend static site from the frontend/ directory."""

    def get(self, request, path=''):
        frontend_dir = settings.FRONTEND_DIR
        path = path.rstrip('/') if path else path

        if not path or path == 'index.html':
            file_path = frontend_dir / 'index.html'
        elif path == 'courses':
            file_path = frontend_dir / 'courses.html'
        elif path == 'articles':
            file_path = frontend_dir / 'articles.html'
        elif COURSE_DETAIL_PATTERN.match(path):
            file_path = frontend_dir / 'course.html'
        elif ARTICLE_DETAIL_PATTERN.match(path):
            file_path = frontend_dir / 'article.html'
        elif path in DEDICATED_PAGES:
            mapped = DEDICATED_PAGES[path]
            candidate = frontend_dir / mapped
            if not candidate.is_file() and mapped == 'register.html':
                candidate = frontend_dir / 'register (1).html'
            file_path = candidate
        elif CATEGORY_PAGE_PATTERN.match(path):
            file_path = frontend_dir / 'courses.html'
        else:
            file_path = (frontend_dir / path).resolve()
            if not str(file_path).startswith(str(frontend_dir.resolve())):
                raise Http404
            if not file_path.is_file():
                if path == 'courses':
                    file_path = frontend_dir / 'courses.html'
                elif path == 'articles':
                    file_path = frontend_dir / 'articles.html'
                elif COURSE_DETAIL_PATTERN.match(path.split('/')[0] if '/' in path else path):
                    file_path = frontend_dir / 'course.html'
                elif ARTICLE_DETAIL_PATTERN.match(path.split('/')[0] if '/' in path else path):
                    file_path = frontend_dir / 'article.html'
                elif CATEGORY_PAGE_PATTERN.match(path.split('/')[0] if '/' in path else path):
                    file_path = frontend_dir / 'courses.html'
                else:
                    file_path = frontend_dir / 'index.html'

        if not file_path.is_file():
            raise Http404

        content_type, _ = mimetypes.guess_type(str(file_path))
        return FileResponse(open(file_path, 'rb'), content_type=content_type or 'application/octet-stream')
