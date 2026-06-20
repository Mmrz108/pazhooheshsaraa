from django.urls import path

from apps.content.views import (
    ArticleDetailView,
    ArticleListView,
    AssociationListView,
    GalleryImagesListView,
    GalleryListView,
    SiteSettingsView,
)

urlpatterns = [
    path('articles/', ArticleListView.as_view(), name='article-list'),
    path('articles/<str:slug>/', ArticleDetailView.as_view(), name='article-detail'),
    path('associations/', AssociationListView.as_view(), name='association-list'),
    path('gallery/', GalleryListView.as_view(), name='gallery-list'),
    path('gallery/images/', GalleryImagesListView.as_view(), name='gallery-images-list'),
    path('settings/', SiteSettingsView.as_view(), name='site-settings'),
]
