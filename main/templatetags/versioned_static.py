import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def versioned_static(path):
    """Like {% static %}, but appends the file's modification time as ?v=.

    Templates and stylesheets change together, so a browser holding an old
    stylesheet at an unchanged URL renders new markup with missing rules. The
    version string changes whenever the file does, which retires that cache.
    """
    url = static(path)
    absolute_path = finders.find(path)

    if absolute_path is None:
        return url

    try:
        version = int(os.path.getmtime(absolute_path))
    except OSError:
        return url

    separator = "&" if "?" in url else "?"

    return f"{url}{separator}v={version}"
