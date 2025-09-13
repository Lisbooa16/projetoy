from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# Endpoint utilitário para retornar preço efetivo
from rest_framework.views import APIView

from products.models import Produto

from .models import RegraPreco, TabelaPreco
from .serializers import RegraPrecoSerializer, TabelaPrecoSerializer


class TabelaPrecoViewSet(viewsets.ModelViewSet):
    queryset = TabelaPreco.objects.prefetch_related("regras").all()
    serializer_class = TabelaPrecoSerializer


class RegraPrecoViewSet(viewsets.ModelViewSet):
    queryset = RegraPreco.objects.select_related("tabela", "produto", "categoria").all()
    serializer_class = RegraPrecoSerializer


class PrecoEfetivoView(APIView):
    def get(self, request):
        produto_id = request.query_params.get("produto_id")
        if not produto_id:
            return Response({"detail": "produto_id é obrigatório."}, status=400)
        produto = Produto.objects.get(pk=produto_id)

        # from pricing.services import get_preco
        # preco = get_preco(produto=produto, dt=timezone.now())

        preco = produto.preco  # placeholder
        return Response({"produto_id": produto.id, "preco_efetivo": str(preco)})
