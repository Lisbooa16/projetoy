from django.apps import apps
from django.contrib.auth.models import Group
from django.db import models

# ajuste o import abaixo para o seu caminho real do modelo de usuário
from custom_auth.models import User as UserProfile


class GroupObjectPermission(models.Model):
    """
    Permissões granulares atribuídas a grupos específicos, com escopo por modelo.
    Cada registro define:
      - Um grupo
      - Uma ação (view, edit, delete, readonly)
      - Lista de modelos onde essa ação é permitida
      - Vários usuários que pertencem a esse grupo e herdam essas permissões
    """

    ACTION_CHOICES = [
        ("view", "Visualizar"),
        ("edit", "Editar"),
        ("delete", "Excluir"),
        ("readonly", "Somente Leitura"),
    ]

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="custom_permissions",
    )
    users = models.ManyToManyField(
        UserProfile,
        related_name="custom_group_permissions",
        blank=True,
    )
    model_names = models.JSONField(default=list)  # ["app_label.model_name", ...]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    class Meta:
        verbose_name = "Permissão Granular de Grupo"
        verbose_name_plural = "Permissões Granulares de Grupos"
        unique_together = ("group", "action")  # evita duplicatas redundantes

    def __str__(self):
        user_count = self.users.count()
        return f"{self.group.name} → {self.action} → {user_count} usuário(s)"

    def save(self, *args, **kwargs):
        """
        Garante que a lista de modelos seja normalizada e sem duplicatas.
        """
        normalized = set()
        for entry in self.model_names:
            # força formato consistente: app_label.model_name
            if "." not in entry:
                # tenta encontrar o app_label correto
                for model in apps.get_models():
                    if model._meta.model_name == entry:
                        entry = f"{model._meta.app_label}.{model._meta.model_name}"
                        break
            normalized.add(entry.lower())
        self.model_names = sorted(normalized)
        super().save(*args, **kwargs)


def get_all_model_choices() -> list[tuple[str, str]]:
    """
    Retorna uma lista de todos os models registrados no Django, para popular choices em forms/admins.
    Exemplo: ("app_label.model_name", "app_label.ModelName")
    """
    choices = []
    for model in apps.get_models():
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        verbose = f"{app_label}.{model.__name__}"
        key = f"{app_label}.{model_name}"
        choices.append((key, verbose))
    return sorted(choices, key=lambda x: x[1])
