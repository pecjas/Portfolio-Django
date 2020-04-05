from django.conf import settings

def google_analytics_head_info(request):
    return {
        "google_analytics_head_info": settings.GOOGLE_ANALYTICS_HEAD_INFO
    }
