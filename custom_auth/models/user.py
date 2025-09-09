from __future__ import annotations

import uuid

from admin_interface.models import Theme as AdminTheme
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Theme(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    # Variáveis CSS (ex.: {"--color-bg":"#0b0b0b","--color-text":"#fafafa","--primary":"#7c3aed"})
    variables = models.JSONField(default=dict, blank=True)

    logo_url = models.URLField(blank=True, null=True)
    favicon_url = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = "Theme"
        verbose_name_plural = "Themes"

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Usuário customizado.
    - Mantém username (mais simples pra começar)
    - E-mail único (opcional, mas comum)
    - UUID público para expor em APIs
    """

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(_("email address"), unique=True)
    display_name = models.CharField(_("display name"), max_length=150, blank=True)

    # exemplo de flag
    is_email_verified = models.BooleanField(default=False)
    theme = models.ForeignKey(
        "custom_auth.Theme",
        on_delete=models.SET_NULL,
        related_name="users",
        null=True,
        blank=True,
    )
    admin_theme = models.ForeignKey(
        AdminTheme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users_with_admin_theme",
        help_text="Tema do django-admin-interface para este usuário.",
    )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self) -> str:
        return self.display_name or self.get_full_name() or self.username
