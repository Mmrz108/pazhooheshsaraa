from django.urls import path

from apps.content.views import (
    AcademyDetailView,
    AcademyListView,
    ArticleDetailView,
    ArticleListView,
    AssociationDetailView,
    AssociationListView,
    FestivalDetailView,
    FestivalListView,
    GalleryImagesListView,
    GalleryListView,
    SiteSettingsView,
)

urlpatterns = [
    path('articles/', ArticleListView.as_view(), name='article-list'),
    path('articles/<str:slug>/', ArticleDetailView.as_view(), name='article-detail'),
    path('associations/', AssociationListView.as_view(), name='association-list'),
    path('associations/<str:slug>/', AssociationDetailView.as_view(), name='association-detail'),
    path('academies/', AcademyListView.as_view(), name='academy-list'),
    path('academies/<str:slug>/', AcademyDetailView.as_view(), name='academy-detail'),
    path('festivals/', FestivalListView.as_view(), name='festival-list'),
    path('festivals/<str:slug>/', FestivalDetailView.as_view(), name='festival-detail'),
    path('gallery/', GalleryListView.as_view(), name='gallery-list'),
    path('gallery/images/', GalleryImagesListView.as_view(), name='gallery-images-list'),
    path('settings/', SiteSettingsView.as_view(), name='site-settings'),
]
