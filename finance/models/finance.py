# finance/models.py
from decimal import Decimal

from django.db import models
from django.utils import timezone

from sales.models.sales import Venda


class Pessoa(models.Model):  # genérico: cliente/fornecedor
    nome = models.CharField(max_length=255)
    documento = models.CharField(max_length=20, blank=True, null=True)


class ContaReceber(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.SET_NULL, null=True, blank=True)
    sacado = models.ForeignKey(
        Pessoa, on_delete=models.PROTECT, related_name="contas_receber"
    )
    descricao = models.CharField(max_length=255)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    emitida_em = models.DateField()
    status = models.CharField(
        max_length=15,
        choices=[("aberta", "Aberta"), ("parcial", "Parcial"), ("paga", "Paga")],
        default="aberta",
    )


class ParcelaReceber(models.Model):
    conta = models.ForeignKey(
        ContaReceber, on_delete=models.CASCADE, related_name="parcelas"
    )
    numero = models.PositiveSmallIntegerField()
    vencimento = models.DateField()
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    pago_em = models.DateField(null=True, blank=True)
    valor_pago = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )


# Espelho para fornecedores:
class ContaPagar(models.Model):
    favorecido = models.ForeignKey(
        Pessoa, on_delete=models.PROTECT, related_name="contas_pagar"
    )
    descricao = models.CharField(max_length=255)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    emitida_em = models.DateField()
    status = models.CharField(
        max_length=15,
        choices=[("aberta", "Aberta"), ("parcial", "Parcial"), ("paga", "Paga")],
        default="aberta",
    )
