from __future__ import annotations

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


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

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self) -> str:
        return self.display_name or self.get_full_name() or self.username
