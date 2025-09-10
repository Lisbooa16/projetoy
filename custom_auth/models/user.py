# apps/custom_auth/models.py
from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

# ... (seus imports + classes Theme/User/Loja/Vendedor que você já tem)

# Se você usa django-admin-interface:
try:
    from admin_interface.models import Theme as AdminTheme
except Exception:  # fallback opcional se o pacote não estiver instalado

    class AdminTheme(models.Model):  # type: ignore
        title = models.CharField(max_length=100)
        active = models.BooleanField(default=False)

        class Meta:
            managed = False  # somente pra evitar migração quando não instalado

        def __str__(self):
            return getattr(self, "title", "Admin Theme")


class Theme(models.Model):
    """
    Tema do FRONT (loja/site). Guarda variáveis CSS e mídias.
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    # Ex.: {"--color-bg":"#0b0b0b","--color-text":"#fafafa","--primary":"#7c3aed"}
    variables = models.JSONField(default=dict, blank=True)

    logo_url = models.URLField(blank=True, null=True)
    favicon_url = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = "Theme"
        verbose_name_plural = "Themes"

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_active(cls) -> Optional["Theme"]:
        """
        Retorna 1 tema ativo (prioriza o mais recente).
        Útil como fallback quando user/loja não definem tema.
        """
        return cls.objects.filter(is_active=True).order_by("-id").first()


class User(AbstractUser):
    """
    Usuário customizado.
    Mantém username + email único.
    Permite atrelar:
      - theme (front)
      - admin_theme (django-admin-interface)
      - lojas (M2M)
    """

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(_("email address"), unique=True)
    display_name = models.CharField(_("display name"), max_length=150, blank=True)

    is_email_verified = models.BooleanField(default=False)

    theme = models.ForeignKey(
        "custom_auth.Theme",
        on_delete=models.SET_NULL,
        related_name="users",
        null=True,
        blank=True,
        help_text="Tema do FRONT preferido deste usuário.",
    )

    admin_theme = models.ForeignKey(
        AdminTheme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users_with_admin_theme",
        help_text="Tema do django-admin-interface para este usuário.",
    )

    # Observação: manteremos M2M mesmo com Loja.dono (FK) para permitir
    # múltiplos usuários colaborando em uma mesma loja.
    lojas = models.ManyToManyField("Loja", related_name="usuarios", blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self) -> str:
        return self.display_name or self.get_full_name() or self.username

    # ---------- Resolução de temas (conveniências) ----------

    def get_effective_front_theme(self, loja: "Loja | None" = None) -> Optional[Theme]:
        """
        Prioridade:
        1) theme definido no usuário
        2) tema da loja informada (ou primeira loja do usuário)
        3) Theme.get_active()
        """
        if self.theme:
            return self.theme

        candidate_loja = loja or self.lojas.order_by("-id").first()
        if candidate_loja and candidate_loja.tema:
            return candidate_loja.tema

        return Theme.get_active()

    def get_effective_admin_theme(self) -> Optional[AdminTheme]:
        """
        Prioridade:
        1) admin_theme definido no usuário
        2) admin_interface Theme ativo (fallback)
        """
        if self.admin_theme:
            return self.admin_theme

        # Fallback: tenta um tema ativo global do admin-interface (se existir)
        try:
            return (
                AdminTheme.objects.filter(Q(active=True) | Q(is_active=True))
                .order_by("-id")
                .first()
            )
        except Exception:
            return None

    @lru_cache(maxsize=512)
    def _collect_front_codenames(self, loja: "Loja | int | None" = None) -> set[str]:
        """
        Junta codenames vindos de:
          - permissões diretas do user (globais + da loja)
          - papéis do user (globais + da loja) e suas permissões
        Aceita loja (objeto) ou loja_id (int).
        """
        loja_id = getattr(loja, "id", loja)

        # diretas (globais)
        direct_global = FrontPermission.objects.filter(
            user_assignments__user=self, user_assignments__loja__isnull=True
        ).values_list("codename", flat=True)

        # diretas (escopo loja)
        direct_scoped = FrontPermission.objects.filter(
            user_assignments__user=self, user_assignments__loja_id=loja_id
        ).values_list("codename", flat=True)

        # via roles globais
        role_global = FrontPermission.objects.filter(
            roles__user_memberships__user=self,
            roles__user_memberships__loja__isnull=True,
        ).values_list("codename", flat=True)

        # via roles da loja
        role_scoped = FrontPermission.objects.filter(
            roles__user_memberships__user=self, roles__user_memberships__loja_id=loja_id
        ).values_list("codename", flat=True)

        return (
            set(direct_global)
            | set(direct_scoped)
            | set(role_global)
            | set(role_scoped)
        )

    def has_front_perm(self, codename: str, loja: "Loja | int | None" = None) -> bool:
        """
        Checa se o usuário possui a permissão de FRONT.
        Se 'loja' for informado, considera (1) perms globais e (2) perms/papéis da loja.
        """
        return codename in self._collect_front_codenames(loja)

    def front_perms(self, loja: "Loja | int | None" = None) -> set[str]:
        """Retorna o conjunto de codenames resolvidos (útil pra debug/UI)."""
        return self._collect_front_codenames(loja)

    def clear_front_perm_cache(self):
        """Chame após mudar papéis/permissões do user na mesma request."""
        try:
            self._collect_front_codenames.cache_clear()
        except Exception:
            pass


class Loja(models.Model):
    """
    Loja/estabelecimento.
    """

    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)

    # Dono principal (FK)
    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lojas_proprietario",
    )

    # Tema do FRONT para esta loja
    tema = models.ForeignKey(
        Theme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lojas",
    )

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Loja"
        verbose_name_plural = "Lojas"
        constraints = [
            models.UniqueConstraint(
                fields=["dono", "nome"], name="uniq_loja_por_dono_nome"
            )
        ]

    def __str__(self) -> str:
        return self.nome

    def get_effective_front_theme(self) -> Optional[Theme]:
        """
        Prioridade da loja:
        1) tema definido na loja
        2) tema do dono (User.theme)
        3) Theme.get_active()
        """
        if self.tema:
            return self.tema
        if getattr(self.dono, "theme", None):
            return self.dono.theme
        return Theme.get_active()


class Vendedor(models.Model):
    """
    Perfil de vendedor acoplado a um User.
    """

    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vendedor")
    nome_loja = models.ForeignKey(
        Loja, on_delete=models.CASCADE, related_name="vendedores"
    )
    descricao_loja = models.TextField(blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vendedor"
        verbose_name_plural = "Vendedores"

    def __str__(self) -> str:
        return (
            self.nome_loja.nome
            if self.nome_loja_id
            else (self.user.username or str(self.pk))
        )


# -------------------- SINAIS DE SINCRONIZAÇÃO --------------------


@receiver(post_save, sender=Loja)
def _sync_loja_m2m_on_create(sender, instance: Loja, created: bool, **kwargs):
    """
    Garante que o dono da Loja também faça parte do M2M `usuarios`.
    """
    if created and instance.dono:
        instance.usuarios.add(instance.dono)


@receiver(post_delete, sender=Loja)
def _cleanup_user_lojas_on_delete(sender, instance: Loja, **kwargs):
    """
    Limpa vínculos M2M com usuários ao deletar a loja.
    (Django já cuida, mas manter explícito ajuda a consistência em alguns casos.)
    """
    instance.usuarios.clear()


class FrontPermission(models.Model):
    """
    Permissão do FRONT. Use codenames estáveis (ex.: "product.view", "product.edit").
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    codename = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Front permission"
        verbose_name_plural = "Front permissions"

    def __str__(self) -> str:
        return f"{self.codename} — {self.name}"


class Role(models.Model):
    """
    Papel (conjunto de permissões). Ex.: 'vendedor', 'gerente', 'dono'.
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(
        FrontPermission, related_name="roles", blank=True
    )

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:
        return self.name


class UserFrontPermission(models.Model):
    """
    Permissão atribuída diretamente ao usuário, opcionalmente escopada por Loja.
    Se loja = NULL, a permissão vale globalmente para o usuário.
    """

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="front_perms_rel",
    )
    permission = models.ForeignKey(
        FrontPermission, on_delete=models.CASCADE, related_name="user_assignments"
    )
    loja = models.ForeignKey(
        "Loja",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="front_perms_rel",
    )

    class Meta:
        verbose_name = "User front permission"
        verbose_name_plural = "User front permissions"
        constraints = [
            UniqueConstraint(
                fields=["user", "permission", "loja"],
                name="uniq_user_front_perm_per_loja",
            ),
        ]

    def __str__(self) -> str:
        scope = self.loja_id and f"@{self.loja_id}" or "@global"
        return f"{self.user_id}:{self.permission.codename}{scope}"


class UserRole(models.Model):
    """
    Papel atribuído ao usuário, opcionalmente escopado por Loja.
    """

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roles_rel"
    )
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="user_memberships"
    )
    loja = models.ForeignKey(
        "Loja",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="roles_rel",
    )

    class Meta:
        verbose_name = "User role"
        verbose_name_plural = "User roles"
        constraints = [
            UniqueConstraint(
                fields=["user", "role", "loja"], name="uniq_user_role_per_loja"
            ),
        ]

    def __str__(self) -> str:
        scope = self.loja_id and f"@{self.loja_id}" or "@global"
        return f"{self.user_id}:{self.role.name}{scope}"
