from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from custom_auth.models.user import Theme

from .forms import UserChangeForm, UserCreationForm
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = ("username", "email", "admin_theme", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "admin_theme")
    search_fields = ("username", "email", "display_name")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Informações pessoais", {"fields": ("first_name", "last_name", "email")}),
        ("Admin theme", {"fields": ("admin_theme",)}),  # 👈 aqui
        (
            "Permissões",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Datas importantes", {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ("public_id",)
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "display_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    actions = ["remover_tema"]

    def remover_tema(self, request, queryset):
        n = queryset.update(theme=None)
        self.message_user(request, f"Tema removido de {n} usuário(s).")

    remover_tema.short_description = "Remover tema"

    def get_actions(self, request):
        actions = super().get_actions(request)
        for t in Theme.objects.filter(is_active=True).order_by("name"):

            def make_action(theme):
                def _action(modeladmin, req, qs):
                    n = qs.update(theme=theme)
                    modeladmin.message_user(
                        req, f"Tema “{theme.name}” aplicado em {n} usuário(s)."
                    )

                _action.__name__ = f"set_theme_{theme.slug}"
                _action.short_description = (
                    f"Atribuir tema → {theme.name} ({theme.slug})"
                )
                return _action

            act = make_action(t)
            actions[act.__name__] = (act, act.__name__, act.short_description)
        return actions
