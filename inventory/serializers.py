from rest_framework import serializers

from inventory.models.inventory import Estoque, MovimentoEstoque


class EstoqueSerializer(serializers.ModelSerializer):
    produto_nome = serializers.ReadOnlyField(source="produto.nome")

    class Meta:
        model = Estoque
        fields = ("id", "produto", "produto_nome", "quantidade", "custo_medio")


class MovimentoEstoqueSerializer(serializers.ModelSerializer):
    produto_nome = serializers.ReadOnlyField(source="produto.nome")

    class Meta:
        model = MovimentoEstoque
        fields = "__all__"
        read_only_fields = ("id", "criado_em")
