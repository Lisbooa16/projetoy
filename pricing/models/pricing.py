# pricing/models.py
from decimal import Decimal

from django.db import models
from django.utils import timezone

from products.models import Categoria, Produto


class TabelaPreco(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    ativo = models.BooleanField(default=True)
    prioridade = models.PositiveSmallIntegerField(
        default=100
    )  # menor = aplica primeiro

    def __str__(self):
        return self.nome


class RegraPreco(models.Model):
    tabela = models.ForeignKey(
        TabelaPreco, on_delete=models.CASCADE, related_name="regras"
    )
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, null=True, blank=True
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, null=True, blank=True
    )
    percentual_desconto = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    preco_fixo = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    combinavel = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["data_inicio", "data_fim"])]

    def ativa(self, dt=None):
        dt = dt or timezone.now()
        return self.data_inicio <= dt <= self.data_fim
