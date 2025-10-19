from django.apps import AppConfig
from django.db.models.signals import post_migrate

class SalesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales'

    def ready(self):
        from .signals import create_default_payment_methods
        create_default_payment_methods()
        import sales.signals