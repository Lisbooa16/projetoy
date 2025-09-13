from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EstoqueViewSet, MovimentoEstoqueViewSet

router = DefaultRouter()
router.register(r"estoque", EstoqueViewSet, basename="estoque")
router.register(r"movimentos", MovimentoEstoqueViewSet, basename="movimento-estoque")

urlpatterns = [
    path("", include(router.urls)),
]
