from rest_framework import serializers

from .models import LancamentoComissao, RegraComissao


class RegraComissaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegraComissao
        fields = "__all__"


class LancamentoComissaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LancamentoComissao
        fields = "__all__"
        read_only_fields = ("criado_em",)
