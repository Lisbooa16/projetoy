from django.urls import path

from .views import (
    EstoqueAtualView,
    EstoqueFaturadoPeriodoView,
    VendasDiarioView,
    VendasMensalView,
)

urlpatterns = [
    path("vendas/diario/", VendasDiarioView.as_view(), name="reports-vendas-diario"),
    path("vendas/mensal/", VendasMensalView.as_view(), name="reports-vendas-mensal"),
    path("estoque/atual/", EstoqueAtualView.as_view(), name="reports-estoque-atual"),
    path(
        "estoque/faturado/",
        EstoqueFaturadoPeriodoView.as_view(),
        name="reports-estoque-faturado",
    ),
]
