from django.http import JsonResponse
from django.views import View


class APIRootView(View):
    def get(self, request):
        return JsonResponse({
            'name': 'Pazhooheshsaraa API',
            'version': '1.0',
            'endpoints': {
                'admin': '/admin/',
                'auth': '/api/auth/',
                'courses': '/api/courses/',
                'payments': '/api/payments/',
                'dashboard': '/api/dashboard/',
                'articles': '/api/articles/',
                'associations': '/api/associations/',
                'gallery': '/api/gallery/',
                'settings': '/api/settings/',
            },
        })
