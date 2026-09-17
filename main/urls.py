from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "main"

urlpatterns = [
    path('', views.index, name='index'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('contact/', views.contact, name='contact'),
    path('projects/<slug:slug>/', views.project, name='project'),

    # Kept so links shared before the move to slugs still resolve.
    path('project/', views.legacy_project_redirect, name='legacy_project'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
