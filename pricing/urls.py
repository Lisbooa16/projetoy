from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PrecoEfetivoView, RegraPrecoViewSet, TabelaPrecoViewSet

router = DefaultRouter()
router.register(r"tabelas", TabelaPrecoViewSet, basename="tabela-preco")
router.register(r"regras", RegraPrecoViewSet, basename="regra-preco")

urlpatterns = [
    path("", include(router.urls)),
    path("preco/", PrecoEfetivoView.as_view(), name="preco-efetivo"),
]
