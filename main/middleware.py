"""Response headers the site needs and Django does not set by default."""


class HtmlRevalidationMiddleware:
    """Makes a browser recheck the HTML on every visit.

    Django sends an ordinary page with no Cache-Control, no ETag and no
    Last-Modified, which leaves the browser to guess how long it stays fresh.
    Browsers guess "reuse it", so a returning visitor kept rendering the
    previous deploy's HTML -- and with it the previous deploy's ?v= stamps, so
    the cache-busted stylesheet was never requested either. The version stamp
    was working; nothing was asking for it.

    "no-cache" does not mean "do not store". It means store it and revalidate
    before reuse. Paired with ConditionalGetMiddleware's ETag, an unchanged
    page costs a 304 and a few hundred bytes rather than a full re-render.

    Responses that already carry a Cache-Control are left alone, so the admin
    keeps the stricter no-store policy Django gives it. Static files are
    untouched either way: they are served outside Django, and their URLs
    already carry a version stamp.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        is_html = response.get("Content-Type", "").startswith("text/html")

        if is_html and not response.has_header("Cache-Control"):
            response["Cache-Control"] = "no-cache"

        return response
