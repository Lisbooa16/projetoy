# sales/models.py
from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from products.models import Categoria, Produto, Promocao


class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    documento = models.CharField(max_length=20, blank=True, null=True)  # CPF/CNPJ
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.nome


class FormaPagamento(models.Model):
    nome = models.CharField(max_length=50)  # Dinheiro, PIX, Cartão crédito, etc.
    exige_parcelamento = models.BooleanField(default=False)

    def __str__(self):
        return self.nome


class Venda(models.Model):
    class Status(models.TextChoices):
        RASCUNHO = "draft", "Rascunho"
        ABERTA = "open", "Aberta"
        FATURADA = "invoiced", "Faturada"
        CANCELADA = "canceled", "Cancelada"

    numero = models.CharField(max_length=30, unique=True, db_index=True)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.SET_NULL, null=True, blank=True
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="vendas",
    )
    forma_pagamento = models.ForeignKey(FormaPagamento, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.RASCUNHO
    )
    desconto_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    acrescimo_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venda {self.numero}"

    def recalcular_totais(self):
        it_sub = sum(i.quantidade * i.preco_unitario for i in self.itens.all())
        it_desc = sum(i.valor_desconto or Decimal("0") for i in self.itens.all())
        self.subtotal = it_sub
        self.total = it_sub - it_desc - self.desconto_total + self.acrescimo_total

    @transaction.atomic
    def fechar(self):
        # validações
        if not self.itens.exists():
            raise ValueError("Venda sem itens.")
        self.status = self.Status.ABERTA
        self.recalcular_totais()
        self.save()


class ItemVenda(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # já com promoção aplicada
    valor_desconto = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    custo_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )  # p/ margem

    def __str__(self):
        return f"{self.produto} x{self.quantidade}"
