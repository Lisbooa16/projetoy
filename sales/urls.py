from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClienteViewSet, FormaPagamentoViewSet, ItemVendaViewSet, VendaViewSet

router = DefaultRouter()
router.register(r"clientes", ClienteViewSet, basename="cliente")
router.register(r"formas-pagamento", FormaPagamentoViewSet, basename="forma-pagamento")
router.register(r"vendas", VendaViewSet, basename="venda")
router.register(r"itens-venda", ItemVendaViewSet, basename="item-venda")

urlpatterns = [
    path("", include(router.urls)),
]
