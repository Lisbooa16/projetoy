from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import LancamentoComissao, RegraComissao
from .serializers import LancamentoComissaoSerializer, RegraComissaoSerializer


class RegraComissaoViewSet(viewsets.ModelViewSet):
    queryset = RegraComissao.objects.select_related(
        "vendedor", "categoria", "produto"
    ).all()
    serializer_class = RegraComissaoSerializer


class LancamentoComissaoViewSet(viewsets.ModelViewSet):
    queryset = LancamentoComissao.objects.select_related(
        "venda", "item", "vendedor"
    ).all()
    serializer_class = LancamentoComissaoSerializer

    @action(detail=True, methods=["post"])
    def marcar_paga(self, request, pk=None):
        lanc = self.get_object()
        lanc.status = "paga"
        lanc.save(update_fields=["status"])
        return Response(LancamentoComissaoSerializer(lanc).data)
