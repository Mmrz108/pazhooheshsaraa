from rest_framework import serializers

from apps.content.models import (
    Article,
    ArticleCategory,
    Association,
    Festival,
    GalleryCategory,
    GalleryImage,
    SiteSettings,
)


class ArticleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleCategory
        fields = ['id', 'title', 'slug']


class ArticleListSerializer(serializers.ModelSerializer):
    category = ArticleCategorySerializer(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'excerpt', 'image', 'category', 'publish_date']

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


class ArticleDetailSerializer(ArticleListSerializer):
    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + ['content']


class AssociationSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Association
        fields = ['id', 'title', 'slug', 'description', 'image']

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


class AssociationDetailSerializer(AssociationSerializer):
    class Meta(AssociationSerializer.Meta):
        fields = AssociationSerializer.Meta.fields + ['content']


class FestivalSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Festival
        fields = ['id', 'title', 'slug', 'description', 'image']

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


class FestivalDetailSerializer(FestivalSerializer):
    class Meta(FestivalSerializer.Meta):
        fields = FestivalSerializer.Meta.fields + ['content']


class GalleryImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    category_title = serializers.CharField(source='category.title', read_only=True)

    class Meta:
        model = GalleryImage
        fields = ['id', 'title', 'image', 'order', 'category_slug', 'category_title', 'created_at']

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


class GalleryCategorySerializer(serializers.ModelSerializer):
    images = GalleryImageSerializer(many=True, read_only=True)

    class Meta:
        model = GalleryCategory
        fields = ['id', 'title', 'slug', 'images']


class SiteSettingsSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    hero_image = serializers.SerializerMethodField()

    class Meta:
        model = SiteSettings
        fields = [
            'logo', 'hero_image', 'about_text',
            'phone', 'email', 'address', 'eitaa_link',
        ]

    def _abs_url(self, field):
        if not field:
            return None
        request = self.context.get('request')
        url = field.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url

    def get_logo(self, obj):
        return self._abs_url(obj.logo)

    def get_hero_image(self, obj):
        return self._abs_url(obj.hero_image)
