from typing import Any, Dict


def _admin_theme_to_vars(t) -> Dict[str, Any]:
    """
    Converte um admin_interface.Theme em variáveis CSS nossas.
    Expanda aqui conforme os campos que você usa no Theme do pacote.
    """
    if not t:
        return {}
    # usamos getattr pra não quebrar se o campo não existir nessa versão do pacote
    return {
        "--color-bg": getattr(t, "background_color", None) or "#ffffff",
        "--color-text": getattr(t, "text_color", None) or "#111827",
        "--primary": getattr(t, "accent_color", None)
        or getattr(t, "link_color", None)
        or "#2563eb",
        "--surface": getattr(t, "module_background_color", None) or "#f3f4f6",
        "--muted": getattr(t, "breadcrumbs_link_color", None) or "#6b7280",
        # extras comuns:
        "--header-bg": getattr(t, "header_background_color", None)
        or getattr(t, "header_color", None)
        or None,
        "--header-text": getattr(t, "header_text_color", None) or None,
        "--link": getattr(t, "link_color", None) or None,
    }


def theme(request):
    """
    Usa o Theme do django-admin-interface escolhido no User.admin_theme.
    Sempre retorna dict.
    """
    theme_vars = {}
    current_theme = None
    try:
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            current_theme = getattr(user, "admin_theme", None)
        theme_vars = _admin_theme_to_vars(current_theme)
    except Exception:
        theme_vars = {}
        current_theme = None
    return {"current_theme": current_theme, "theme_vars": theme_vars}
