from django.db.models import Q
from django.utils import timezone


def visible_on_site_q(*, prefix=''):
    """Active courses shown on the public site."""
    field = f'{prefix}__' if prefix else ''
    return Q(**{f'{field}is_active': True})


def open_for_registration_q(*, prefix=''):
    """Active courses that still accept new registrations."""
    today = timezone.localdate()
    field = f'{prefix}__' if prefix else ''
    return visible_on_site_q(prefix=prefix) & (
        Q(**{f'{field}registration_deadline__isnull': True})
        | Q(**{f'{field}registration_deadline__gte': today})
    )
