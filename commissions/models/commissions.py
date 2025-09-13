# commissions/models.py
from decimal import Decimal

from django.conf import settings
from django.db import models

from products.models import Categoria, Produto
from sales.models.sales import ItemVenda, Venda


class RegraComissao(models.Model):
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True
    )
    produto = models.ForeignKey(
        Produto, on_delete=models.SET_NULL, null=True, blank=True
    )
    percentual = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )  # % sobre (preco - custo) ou sobre venda
    base_calculo = models.CharField(
        max_length=10,
        choices=[("receita", "Receita"), ("margem", "Margeinventorym")],
        default="margem",
    )
    ativo = models.BooleanField(default=True)
    prioridade = models.PositiveSmallIntegerField(default=100)


class LancamentoComissao(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name="comissoes")
    item = models.ForeignKey(ItemVenda, on_delete=models.CASCADE)
    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=12,
        choices=[("aberta", "Aberta"), ("paga", "Paga")],
        default="aberta",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
