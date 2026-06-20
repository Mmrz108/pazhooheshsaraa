from django.urls import path

from apps.courses.views import (
    CourseCategoryDetailView,
    CourseCategoryListView,
    CourseDetailView,
    CourseListView,
)

urlpatterns = [
    path('categories/', CourseCategoryListView.as_view(), name='course-category-list'),
    path('categories/<str:slug>/', CourseCategoryDetailView.as_view(), name='course-category-detail'),
    path('', CourseListView.as_view(), name='course-list'),
    path('<str:slug>/', CourseDetailView.as_view(), name='course-detail'),
]
