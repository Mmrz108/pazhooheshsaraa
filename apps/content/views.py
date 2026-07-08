from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.content.models import Article, Association, Festival, GalleryCategory, GalleryImage, SiteSettings
from apps.content.serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    AssociationDetailSerializer,
    AssociationSerializer,
    FestivalDetailSerializer,
    FestivalSerializer,
    GalleryCategorySerializer,
    GalleryImageSerializer,
    SiteSettingsSerializer,
)


class ArticleListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ArticleListSerializer

    def get_queryset(self):
        qs = Article.objects.filter(
            is_published=True,
            publish_date__lte=timezone.now(),
        ).select_related('category').order_by('-publish_date')
        limit = self.request.query_params.get('limit')
        if limit and limit.isdigit():
            qs = qs[:int(limit)]
        return qs


class ArticleDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ArticleDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Article.objects.filter(
            is_published=True,
            publish_date__lte=timezone.now(),
        ).select_related('category')

    def get_object(self):
        try:
            return self.get_queryset().get(slug=self.kwargs['slug'])
        except Article.DoesNotExist as exc:
            raise NotFound('مقاله یافت نشد.') from exc


class AssociationListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AssociationSerializer
    queryset = Association.objects.filter(is_active=True)


class AssociationDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AssociationDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Association.objects.filter(is_active=True)

    def get_object(self):
        try:
            return self.get_queryset().get(slug=self.kwargs['slug'])
        except Association.DoesNotExist as exc:
            raise NotFound('انجمن یافت نشد.') from exc


class FestivalListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = FestivalSerializer
    queryset = Festival.objects.filter(is_active=True)


class FestivalDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = FestivalDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Festival.objects.filter(is_active=True)

    def get_object(self):
        try:
            return self.get_queryset().get(slug=self.kwargs['slug'])
        except Festival.DoesNotExist as exc:
            raise NotFound('جشنواره یافت نشد.') from exc


class GalleryListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = GalleryCategorySerializer

    def get_queryset(self):
        return GalleryCategory.objects.prefetch_related('images').all()


class GalleryImagesListView(generics.ListAPIView):
    """Flat list of latest gallery images for homepage."""
    permission_classes = [permissions.AllowAny]
    serializer_class = GalleryImageSerializer

    def get_queryset(self):
        qs = GalleryImage.objects.select_related('category').order_by('-created_at', 'order')
        limit = self.request.query_params.get('limit')
        if limit and limit.isdigit():
            qs = qs[:int(limit)]
        return qs


class SiteSettingsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        settings_obj = SiteSettings.load()
        serializer = SiteSettingsSerializer(settings_obj, context={'request': request})
        return Response(serializer.data)
