from rest_framework import serializers

from products.models import Produto

from .models import Cliente, FormaPagamento, ItemVenda, Venda


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"


class FormaPagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormaPagamento
        fields = "__all__"


class ItemVendaSerializer(serializers.ModelSerializer):
    produto_nome = serializers.ReadOnlyField(source="produto.nome")

    class Meta:
        model = ItemVenda
        fields = (
            "id",
            "venda",
            "produto",
            "produto_nome",
            "quantidade",
            "preco_unitario",
            "valor_desconto",
            "custo_unitario",
        )
        read_only_fields = ("id",)


class VendaSerializer(serializers.ModelSerializer):
    itens = ItemVendaSerializer(many=True, read_only=True)

    class Meta:
        model = Venda
        fields = (
            "id",
            "numero",
            "cliente",
            "vendedor",
            "forma_pagamento",
            "status",
            "desconto_total",
            "acrescimo_total",
            "subtotal",
            "total",
            "criado_em",
            "itens",
        )
        read_only_fields = ("id", "status", "subtotal", "total", "criado_em")
