# inventory/models.py
from decimal import Decimal

from django.db import models
from django.utils import timezone

from products.models import Produto


class Estoque(models.Model):
    produto = models.OneToOneField(
        Produto, on_delete=models.CASCADE, related_name="estoque_registro"
    )
    quantidade = models.PositiveIntegerField(default=0)
    custo_medio = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    @property
    def estoque_atual(self):
        try:
            return self.estoque_registro.quantidade
        except Exception:
            return (
                self.estoque
            )  # fallback se ainda não criou o registro no app inventory


class MovimentoEstoque(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        SAIDA = "saida", "Saída"
        AJUSTE = "ajuste", "Ajuste"

    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    quantidade = models.PositiveIntegerField()
    custo_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )  # p/ entrada/ajuste
    motivo = models.CharField(max_length=255, blank=True, null=True)
    referencia = models.CharField(
        max_length=50, blank=True, null=True
    )  # ex: Venda.numero, NF de compra
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        indexes = [models.Index(fields=["produto", "criado_em"])]
