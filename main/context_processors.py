from django.conf import settings

def google_analytics_head_info(request):
    return {
        "google_analytics_head_info": settings.GOOGLE_ANALYTICS_HEAD_INFO
    }


def site_links(request):
    """Optional off-site profile links. Empty values render nothing."""
    return {
        "linkedin_url": getattr(settings, "LINKEDIN_URL", ""),
    }
