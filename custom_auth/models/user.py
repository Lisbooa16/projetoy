from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

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

    lojas = models.ManyToManyField("Loja", related_name="usuarios", blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self) -> str:
        return self.display_name or self.get_full_name() or self.username

    # ---------- Resolução de temas ----------

    def get_effective_front_theme(self, loja: "Loja | None" = None) -> Optional[Theme]:
        if self.theme:
            return self.theme

        candidate_loja = loja or self.lojas.order_by("-id").first()
        if candidate_loja and candidate_loja.tema:
            return candidate_loja.tema

        return Theme.get_active()

    def get_effective_admin_theme(self) -> Optional[AdminTheme]:
        if self.admin_theme:
            return self.admin_theme

        try:
            return (
                AdminTheme.objects.filter(Q(active=True) | Q(is_active=True))
                .order_by("-id")
                .first()
            )
        except Exception:
            return None

    # ---------- Permissões do FRONT ----------

    @lru_cache(maxsize=512)
    def _collect_front_codenames(self, loja: "Loja | int | None" = None) -> set[str]:
        loja_id = getattr(loja, "id", loja)

        direct_global = FrontPermission.objects.filter(
            user_assignments__user=self, user_assignments__loja__isnull=True
        ).values_list("codename", flat=True)

        direct_scoped = FrontPermission.objects.filter(
            user_assignments__user=self, user_assignments__loja_id=loja_id
        ).values_list("codename", flat=True)

        role_global = FrontPermission.objects.filter(
            roles__user_memberships__user=self,
            roles__user_memberships__loja__isnull=True,
        ).values_list("codename", flat=True)

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
        return codename in self._collect_front_codenames(loja)

    def front_perms(self, loja: "Loja | int | None" = None) -> set[str]:
        return self._collect_front_codenames(loja)

    def clear_front_perm_cache(self):
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

    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lojas_proprietario",
    )

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

    @property
    def loja(self) -> Loja:
        return self.nome_loja


# -------------------- PERMISSÕES DO FRONT --------------------


class FrontPermission(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    codename = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Front permission"
        verbose_name_plural = "Front permissions"

    def __str__(self) -> str:
        return f"{self.codename} — {self.name}"


class Role(models.Model):
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
        indexes = [
            models.Index(fields=["user", "loja"], name="idx_ufp_user_loja"),
        ]

    def __str__(self) -> str:
        scope = self.loja_id and f"@{self.loja_id}" or "@global"
        return f"{self.user_id}:{self.permission.codename}{scope}"


class UserRole(models.Model):
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
        indexes = [
            models.Index(fields=["user", "loja"], name="idx_ur_user_loja"),
        ]

    def __str__(self) -> str:
        scope = self.loja_id and f"@{self.loja_id}" or "@global"
        return f"{self.user_id}:{self.role.name}{scope}"


# -------------------- SINAIS --------------------


@receiver(post_save, sender=Loja)
def _sync_loja_m2m_on_create(sender, instance: Loja, created: bool, **kwargs):
    if created and instance.dono:
        instance.usuarios.add(instance.dono)


@receiver(post_delete, sender=Loja)
def _cleanup_user_lojas_on_delete(sender, instance: Loja, **kwargs):
    instance.usuarios.clear()


# --------- INVALIDAÇÃO AUTOMÁTICA DO CACHE DE PERMISSÕES ---------


@receiver([post_save, post_delete], sender=UserFrontPermission)
def _invalidate_user_perm_cache_for_direct(
    sender, instance: UserFrontPermission, **kwargs
):
    try:
        instance.user.clear_front_perm_cache()
    except Exception:
        pass


@receiver([post_save, post_delete], sender=UserRole)
def _invalidate_user_perm_cache_for_role(sender, instance: UserRole, **kwargs):
    try:
        instance.user.clear_front_perm_cache()
    except Exception:
        pass


@receiver(m2m_changed, sender=Role.permissions.through)
def _invalidate_role_permissions_changed(sender, instance: Role, action, **kwargs):
    if action not in {"post_add", "post_remove", "post_clear"}:
        return
    try:
        user_ids = list(instance.user_memberships.values_list("user_id", flat=True))
        for uid in set(user_ids):
            from custom_auth.models import User

            try:
                u = User.objects.get(pk=uid)
                u.clear_front_perm_cache()
            except User.DoesNotExist:
                continue
    except Exception:
        pass
