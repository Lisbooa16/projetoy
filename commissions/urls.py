from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LancamentoComissaoViewSet, RegraComissaoViewSet

router = DefaultRouter()
router.register(r"regras", RegraComissaoViewSet, basename="regra-comissao")
router.register(
    r"lancamentos", LancamentoComissaoViewSet, basename="lancamento-comissao"
)

urlpatterns = [
    path("", include(router.urls)),
]
