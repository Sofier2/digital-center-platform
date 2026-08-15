from django import template


register = template.Library()


@register.filter
def dict_get(mapping, key):
    if mapping is None:
        return None
    return mapping.get(key)


def _file_name(value):
    return str(getattr(value, "name", value) or "").lower()


@register.filter
def is_image_file(value):
    return _file_name(value).endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"))


@register.filter
def is_video_file(value):
    return _file_name(value).endswith((".mp4", ".webm", ".mov", ".m4v", ".avi"))


@register.filter
def basename(value):
    return str(getattr(value, "name", value) or "").rsplit("/", 1)[-1]
