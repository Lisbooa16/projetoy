# apps/custom_auth/management/commands/seed_front_perms.py
from django.apps import apps
from django.core.management.base import BaseCommand

from custom_auth.models import FrontPermission


class Command(BaseCommand):
    help = "Seed automático das permissões de FRONT com base nos modelos registrados"

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for model in apps.get_models():
            model_name = model._meta.model_name
            verbose_name = model._meta.verbose_name.title()
            app_label = model._meta.app_label

            # Permissões padrão do Django
            base_perms = [
                ("view", f"Listar/visualizar {verbose_name}"),
                ("add", f"Criar {verbose_name}"),
                ("change", f"Atualizar {verbose_name}"),
                ("delete", f"Excluir {verbose_name}"),
            ]

            for action, desc in base_perms:
                codename = f"{app_label}.{model_name}.{action}"

                obj, was_created = FrontPermission.objects.get_or_create(
                    codename=codename, defaults={"name": desc}
                )

                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Permissões geradas: {created} novas, {skipped} já existiam."
            )
        )
