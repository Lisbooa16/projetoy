from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ContaPagar, ContaReceber, ParcelaReceber, Pessoa
from .serializers import (
    ContaPagarSerializer,
    ContaReceberSerializer,
    ParcelaReceberSerializer,
    PessoaSerializer,
)


class PessoaViewSet(viewsets.ModelViewSet):
    queryset = Pessoa.objects.all().order_by("nome")
    serializer_class = PessoaSerializer


class ContaReceberViewSet(viewsets.ModelViewSet):
    queryset = (
        ContaReceber.objects.select_related("venda", "sacado")
        .prefetch_related("parcelas")
        .all()
    )
    serializer_class = ContaReceberSerializer

    @action(detail=True, methods=["post"])
    def baixa(self, request, pk=None):
        conta = self.get_object()
        hoje = timezone.now().date()
        parcial = request.data.get("parcial", False)
        valor = request.data.get("valor")  # string/decimal opcional

        alterou = False
        for p in conta.parcelas.all().order_by("numero"):
            if p.pago_em:
                continue
            if parcial and valor:
                from decimal import Decimal

                v = Decimal(str(valor))
                if v <= 0:
                    break
                if v >= p.valor:
                    p.pago_em = hoje
                    p.valor_pago = p.valor
                    v -= p.valor
                    alterou = True
                else:
                    p.valor_pago = v
                    p.pago_em = hoje
                    v = 0
                    alterou = True
                p.save(update_fields=["pago_em", "valor_pago"])
                valor = str(v)
                if v == 0:
                    break
            else:
                p.pago_em = hoje
                p.valor_pago = p.valor
                p.save(update_fields=["pago_em", "valor_pago"])
                alterou = True

        if alterou:
            if all(pp.pago_em for pp in conta.parcelas.all()):
                conta.status = "paga"
                conta.save(update_fields=["status"])
        return Response(ContaReceberSerializer(conta).data)


class ParcelaReceberViewSet(viewsets.ModelViewSet):
    queryset = ParcelaReceber.objects.select_related("conta").all()
    serializer_class = ParcelaReceberSerializer


class ContaPagarViewSet(viewsets.ModelViewSet):
    queryset = ContaPagar.objects.select_related("favorecido").all()
    serializer_class = ContaPagarSerializer
