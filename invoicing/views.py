from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import NotaFiscal
from .serializers import NotaFiscalSerializer


class NotaFiscalViewSet(viewsets.ModelViewSet):
    queryset = NotaFiscal.objects.select_related("venda").all()
    serializer_class = NotaFiscalSerializer

    @action(detail=True, methods=["post"])
    def emitir(self, request, pk=None):
        nfe = self.get_object()
        # from invoicing.services import emitir_nfe
        # emitir_nfe(nfe.venda_id)
        nfe.status = "autorizada"  # placeholder
        nfe.save(update_fields=["status"])
        return Response(NotaFiscalSerializer(nfe).data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        nfe = self.get_object()
        # from invoicing.services import cancelar_nfe
        # cancelar_nfe(nfe.id)
        nfe.status = "cancelada"  # placeholder
        nfe.save(update_fields=["status"])
        return Response(NotaFiscalSerializer(nfe).data)
