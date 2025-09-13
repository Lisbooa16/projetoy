from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ContaPagarViewSet,
    ContaReceberViewSet,
    ParcelaReceberViewSet,
    PessoaViewSet,
)

router = DefaultRouter()
router.register(r"pessoas", PessoaViewSet, basename="pessoa")
router.register(r"contas-receber", ContaReceberViewSet, basename="conta-receber")
router.register(r"parcelas-receber", ParcelaReceberViewSet, basename="parcela-receber")
router.register(r"contas-pagar", ContaPagarViewSet, basename="conta-pagar")

urlpatterns = [
    path("", include(router.urls)),
]
