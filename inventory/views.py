from rest_framework import viewsets

from inventory.models.inventory import Estoque, MovimentoEstoque

from .serializers import EstoqueSerializer, MovimentoEstoqueSerializer


class EstoqueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Estoque.objects.select_related("produto").all()
    serializer_class = EstoqueSerializer


class MovimentoEstoqueViewSet(viewsets.ModelViewSet):
    queryset = (
        MovimentoEstoque.objects.select_related("produto").all().order_by("-criado_em")
    )
    serializer_class = MovimentoEstoqueSerializer
