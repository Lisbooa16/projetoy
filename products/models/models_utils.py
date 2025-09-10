from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at", "-updated_at"]
        get_latest_by = "created_at"


class SoftDeletableModel(models.Model):
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ["is_deleted", "-created_at", "-updated_at"]
        get_latest_by = "created_at"


class ActiveModel(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["-is_active", "-created_at", "-updated_at"]
        get_latest_by = "created_at"


class BaseModel(TimeStampedModel, SoftDeletableModel, ActiveModel):
    class Meta:
        abstract = True
        ordering = ["is_deleted", "-is_active", "-created_at", "-updated_at"]
        get_latest_by = "created_at"


# Outros modelos utilitários podem ser adicionados aqui
# como modelos para auditoria, controle de versões, etc.
# Exemplo:
