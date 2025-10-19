from __future__ import annotations

from typing import Optional

from django.http import HttpRequest
from rest_framework.permissions import SAFE_METHODS, BasePermission

from custom_auth.models import GroupObjectPermission

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


def has_group_action(user, model_name: str, action: str) -> bool:
    """
    Verifica se o usuário possui permissão (por grupo ou direta)
    para executar uma ação (view/edit/delete/readonly)
    em um determinado modelo.
    Compatível com SQLite e bancos sem JSONField lookups.
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    model_name = model_name.lower()
    action = action.lower()

    # 🔹 1. Permissões diretas via allowed_actions
    if (
        hasattr(user, "allowed_actions")
        and user.allowed_actions.filter(
            model_name=model_name, name__iexact=action
        ).exists()
    ):
        return True

    # 🔹 2. Permissões via GroupObjectPermission
    groups = user.groups.all()
    if not groups.exists():
        return False

    # ⚠️ Não usar JSON lookup (__contains) → filtra todos e verifica em Python
    qs = GroupObjectPermission.objects.filter(
        users=user, group__in=groups, action=action
    )

    for g in qs:
        # normaliza nomes (aceita 'app.Model', 'Model', 'user', etc.)
        normalized = g.model_names
        if model_name in normalized:
            return True

    return False


def has_group_action_libera(user, model_name: str, action_name: str) -> bool:
    """
    Variante usada para validar 'actions' customizadas no Django Admin.
    Exemplo: 'exportar_relatorio', 'gerar_pdf', etc.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    model_name = model_name.lower()
    action_name = action_name.strip().lower()

    # 🔹 1. Verifica se o usuário tem permissão direta via allowed_actions
    if (
        hasattr(user, "allowed_actions")
        and user.allowed_actions.filter(
            model_name=model_name, name__iexact=action_name
        ).exists()
    ):
        return True

    # 🔹 2. Verifica permissões via GroupObjectPermission
    groups = user.groups.all()
    if GroupObjectPermission.objects.filter(
        group__in=groups,
        action__in=["edit", "view", "readonly"],  # apenas actions genéricas
        model_names__contains=[model_name],
    ).exists():
        return True

    # 🔹 3. (Fallback) — compatibilidade com permissões Django nativas
    codename = f"{model_name}_{action_name}"
    if user.user_permissions.filter(codename=codename).exists():
        return True
    if user.groups.filter(permissions__codename=codename).exists():
        return True

    return False
