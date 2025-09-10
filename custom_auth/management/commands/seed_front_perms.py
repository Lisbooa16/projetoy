# apps/custom_auth/management/commands/seed_front_perms.py
from django.core.management.base import BaseCommand

from custom_auth.models import FrontPermission

PERMS = [
    ("category.view", "Listar/visualizar categorias"),
    ("category.create", "Criar categoria"),
    ("category.update", "Atualizar categoria"),
    ("category.delete", "Excluir categoria"),
    ("product.view", "Listar/visualizar produtos"),
    ("product.create", "Criar produto"),
    ("product.update", "Atualizar produto"),
    ("product.delete", "Excluir produto"),
    ("promotion.view", "Listar/visualizar promoções"),
    ("promotion.manage", "Criar/atualizar/excluir promoções"),
]


class Command(BaseCommand):
    help = "Seed de permissões de FRONT"

    def handle(self, *args, **options):
        created = 0
        for code, name in PERMS:
            obj, was_created = FrontPermission.objects.get_or_create(
                codename=code, defaults={"name": name}
            )
            created += 1 if was_created else 0
        self.stdout.write(
            self.style.SUCCESS(f"OK. Criadas {created} novas permissões.")
        )
