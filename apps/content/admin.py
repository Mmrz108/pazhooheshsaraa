from django.contrib import admin

from apps.content.models import (
    Article,
    ArticleCategory,
    Association,
    Festival,
    SiteSettings,
)


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'publish_date', 'is_published']
    list_filter = ['is_published', 'category', 'publish_date']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'


@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'description', 'content']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['order', 'is_active']


@admin.register(Festival)
class FestivalAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'description', 'content']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['order', 'is_active']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('برندینگ', {'fields': ('logo', 'hero_image', 'about_text')}),
        ('تماس', {'fields': ('phone', 'email', 'address', 'eitaa_link')}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
