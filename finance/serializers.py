from rest_framework import serializers

from .models import ContaPagar, ContaReceber, ParcelaReceber, Pessoa


class PessoaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pessoa
        fields = "__all__"


class ParcelaReceberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParcelaReceber
        fields = "__all__"


class ContaReceberSerializer(serializers.ModelSerializer):
    parcelas = ParcelaReceberSerializer(many=True, read_only=True)

    class Meta:
        model = ContaReceber
        fields = "__all__"


class ContaPagarSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContaPagar
        fields = "__all__"
