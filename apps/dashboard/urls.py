from django.urls import path

from apps.dashboard.views import EnrolledCoursesView, PaymentHistoryView, ProfileView

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='dashboard-profile'),
    path('courses/', EnrolledCoursesView.as_view(), name='dashboard-courses'),
    path('payments/', PaymentHistoryView.as_view(), name='dashboard-payments'),
]
