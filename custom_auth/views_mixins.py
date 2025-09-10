# apps/custom_auth/views_mixins.py
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from .permissions import HasFrontPerm


class BaseFrontPerm(GenericAPIView):
    """
    View base para aplicar autenticação e checagem de permissões de front.

    Uso:
        class ProdutoView(BaseFrontPerm):
            serializer_class = ProdutoSerializer
            required_perm_map = {
                "GET": "product.view",
                "POST": "product.create",
                "PUT": "product.update",
                "DELETE": "product.delete",
            }
    """

    permission_classes = [IsAuthenticated, HasFrontPerm]
    required_perm_map: dict[str, str] = {}

    def get_required_permissions(self):
        """
        Retorna o dicionário de permissões exigidas por método HTTP.
        Override se precisar customizar por view.
        """
        return getattr(self, "required_perm_map", {})
