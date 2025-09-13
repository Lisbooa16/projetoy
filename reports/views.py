# reports/views.py
from __future__ import annotations

from decimal import Decimal

from django.db.models import Count, F, Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models.inventory import Estoque
from sales.models import ItemVenda, Venda


class VendasDiarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoje = timezone.localdate()
        qs = Venda.objects.filter(
            criado_em__date=hoje,
            status__in=["open", "invoiced", "FATURADA", "invoiced".lower()],
        )
        total = qs.aggregate(total=Sum("total"), qtd=Count("id"))
        return Response(
            {
                "data": str(hoje),
                "qtd_vendas": total["qtd"] or 0,
                "total_vendas": str(total["total"] or Decimal("0.00")),
            }
        )


class VendasMensalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now()
        qs = Venda.objects.filter(
            criado_em__year=today.year,
            criado_em__month=today.month,
            status__in=["open", "invoiced", "FATURADA", "invoiced".lower()],
        )
        total = qs.aggregate(total=Sum("total"), qtd=Count("id"))
        return Response(
            {
                "ano": today.year,
                "mes": today.month,
                "qtd_vendas": total["qtd"] or 0,
                "total_vendas": str(total["total"] or Decimal("0.00")),
            }
        )


class EstoqueAtualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Estoque.objects.select_related("produto")
        # valor em custo:
        total_custo = qs.aggregate(v=Sum(F("quantidade") * F("custo_medio")))[
            "v"
        ] or Decimal("0.00")
        # lista resumida
        items = list(
            qs.values("produto__id", "produto__nome", "quantidade", "custo_medio")
        )
        return Response(
            {
                "itens": items,
                "custo_total": str(total_custo),
            }
        )


class EstoqueFaturadoPeriodoView(APIView):
    """
    Soma do custo faturado no período: sum(item.quantidade * item.custo_unitario) para vendas faturadas.
    Query params: ?inicio=YYYY-MM-DD&fim=YYYY-MM-DD
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        inicio = request.query_params.get("inicio")
        fim = request.query_params.get("fim")
        qs = ItemVenda.objects.select_related("venda")

        if inicio:
            qs = qs.filter(venda__criado_em__date__gte=inicio)
        if fim:
            qs = qs.filter(venda__criado_em__date__lte=fim)

        qs = qs.filter(venda__status__in=["invoiced", "FATURADA", "invoiced".lower()])

        total_custo = qs.aggregate(v=Sum(F("quantidade") * F("custo_unitario")))[
            "v"
        ] or Decimal("0.00")

        return Response(
            {
                "inicio": inicio,
                "fim": fim,
                "custo_faturado": str(total_custo),
            }
        )
