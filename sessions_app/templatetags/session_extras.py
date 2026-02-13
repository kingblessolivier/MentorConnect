from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def duration_minutes(start, end):
    """Return duration between two datetimes in whole minutes.

    Usage: {{ start|duration_minutes:end }}
    """
    if not start or not end:
        return ''
    try:
        # Ensure datetimes are timezone-aware consistently
        if timezone.is_naive(start):
            start = timezone.make_aware(start)
        if timezone.is_naive(end):
            end = timezone.make_aware(end)
        total_seconds = (end - start).total_seconds()
        minutes = int(total_seconds // 60)
        return minutes
    except Exception:
        return ''
