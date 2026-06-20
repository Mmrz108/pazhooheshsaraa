"""
URL configuration for pazhooheshsaraa project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from common.frontend import FrontendView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/courses/', include('apps.courses.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/', include('apps.content.urls')),
    re_path(
        r'^media/(?P<path>.*)$',
        serve,
        {'document_root': settings.MEDIA_ROOT},
    ),
    # Frontend — must be last (catch-all for static files)
    path('', FrontendView.as_view(), name='frontend-index'),
    re_path(r'^(?!api/|admin/|media/)(?P<path>.+)$', FrontendView.as_view(), name='frontend-files'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'پژوهشسرا - پنل مدیریت'
admin.site.site_title = 'پژوهشسرا'
admin.site.index_title = 'مدیریت مرکز پژوهشی آموزشی'
