from django.apps import AppConfig


class FastingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "healthy_herron.fasting"
    verbose_name = "Fasting Tracker"

    def ready(self):
        """Import signals when the app is ready."""
        import healthy_herron.fasting.signals  # noqa: F401
