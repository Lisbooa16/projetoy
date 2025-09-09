from django.apps import apps
from django.core.management.base import BaseCommand

from custom_auth.signals import create_default_groups


class Command(BaseCommand):
    help = "Cria/atualiza grupos e permissões padrão do custom_auth"

    def handle(self, *args, **options):
        app_config = apps.get_app_config("custom_auth")
        create_default_groups(sender=app_config)
        self.stdout.write(self.style.SUCCESS("Grupos/permissões atualizados."))
