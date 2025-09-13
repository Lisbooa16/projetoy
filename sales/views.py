from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from products.models import Produto

from .models import Cliente, FormaPagamento, ItemVenda, Venda
from .serializers import (
    ClienteSerializer,
    FormaPagamentoSerializer,
    ItemVendaSerializer,
    VendaSerializer,
)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by("nome")
    serializer_class = ClienteSerializer


class FormaPagamentoViewSet(viewsets.ModelViewSet):
    queryset = FormaPagamento.objects.all().order_by("nome")
    serializer_class = FormaPagamentoSerializer


class ItemVendaViewSet(viewsets.ModelViewSet):
    queryset = ItemVenda.objects.select_related("venda", "produto").all()
    serializer_class = ItemVendaSerializer


class VendaViewSet(viewsets.ModelViewSet):
    queryset = Venda.objects.select_related(
        "cliente", "vendedor", "forma_pagamento"
    ).prefetch_related("itens")
    serializer_class = VendaSerializer

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def adicionar_item(self, request, pk=None):
        venda = self.get_object()
        data = request.data.copy()
        data["venda"] = venda.id

        # Se quiser aplicar promo/tabela aqui, calcule preco_unitario antes de validar
        # from pricing.services import get_preco
        # produto = get_object_or_404(Produto, pk=data["produto"])
        # data["preco_unitario"] = get_preco(produto=produto)

        serializer = ItemVendaSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        venda.recalcular_totais()
        venda.save(update_fields=["subtotal", "total"])
        return Response(ItemVendaSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def fechar(self, request, pk=None):
        venda = self.get_object()
        venda.fechar()
        return Response(VendaSerializer(venda).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def faturar(self, request, pk=None):
        venda = self.get_object()
        # from sales.services import faturar_venda
        # faturar_venda(venda.id, emitir_nfe=request.data.get("emitir_nfe", False))
        venda.status = venda.Status.FATURADA
        venda.save(update_fields=["status"])
        return Response(VendaSerializer(venda).data)
