from __future__ import annotations

from typing import Optional

from django.http import HttpRequest
from rest_framework.permissions import SAFE_METHODS, BasePermission

LOJA_KWARG = "loja_id"  # se a URL for /lojas/<loja_id>/...
LOJA_QUERY = "loja_id"  # ?loja_id=123
LOJA_HEADER = "HTTP_X_LOJA_ID"  # Header: X-Loja-Id: 123


def _extract_loja_id(request: HttpRequest, view) -> Optional[int]:
    # 1) kwargs
    loja_id = (
        request.parser_context.get("kwargs", {}).get(LOJA_KWARG)
        if hasattr(request, "parser_context")
        else None
    )
    if loja_id:
        return int(loja_id)
    # 2) query string
    q = request.query_params.get(LOJA_QUERY)
    if q:
        return int(q)
    # 3) header
    h = request.META.get(LOJA_HEADER)
    if h:
        return int(h)
    return None


class HasFrontPerm(BasePermission):
    """
    Resolve a permissão a partir do método HTTP usando 'required_perm_map' definido na view.
    Ex.: required_perm_map = {"GET": "category.view", "POST": "category.create", ...}
    """

    message = "Você não possui permissão para esta operação."

    def has_permission(self, request, view) -> bool:
        # Sem mapa definido -> não exige permissão extra além de IsAuthenticated
        perm_map = getattr(view, "required_perm_map", None)
        if not perm_map:
            return True

        codename = perm_map.get(request.method)
        if (
            not codename
        ):  # método não mapeado = liberar (ou troque para False se quiser bloquear)
            return True

        loja_id = _extract_loja_id(request, view)

        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.has_front_perm(codename, loja=loja_id)
        )


class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_superuser:
            return True
        return obj == request.user


class IsReadOnlyOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS) or (
            request.user and request.user.is_staff
        )
