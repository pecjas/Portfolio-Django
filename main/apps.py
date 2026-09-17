from django.apps import AppConfig

class MainConfig(AppConfig):
    name = 'main'

    # Pinned to the existing column type. Switching to BigAutoField would be a
    # table rebuild on every model for no benefit at this size.
    default_auto_field = 'django.db.models.AutoField'
