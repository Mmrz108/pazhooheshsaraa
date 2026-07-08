"""Hide unused models from the Django admin index."""


def customize_admin_site():
    from django.contrib import admin
    from django.contrib.auth.models import Group

    admin.site.unregister(Group)

    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        admin.site.unregister(OutstandingToken)
        admin.site.unregister(BlacklistedToken)
    except admin.sites.NotRegistered:
        pass

    try:
        from apps.content.models import GalleryCategory, GalleryImage

        admin.site.unregister(GalleryCategory)
        admin.site.unregister(GalleryImage)
    except admin.sites.NotRegistered:
        pass
