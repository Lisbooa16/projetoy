from rest_framework import serializers

from .models import RegraPreco, TabelaPreco


class RegraPrecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegraPreco
        fields = "__all__"


class TabelaPrecoSerializer(serializers.ModelSerializer):
    regras = RegraPrecoSerializer(many=True, read_only=True)

    class Meta:
        model = TabelaPreco
        fields = ("id", "nome", "ativo", "prioridade", "regras")
