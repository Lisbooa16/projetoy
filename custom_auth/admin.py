from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

# Importa tudo do próprio app (evita caminho errado tipo custom_auth.models.user)
from .models import (
    FrontPermission,
    Loja,
    Role,
    User,
    UserFrontPermission,
    UserRole,
    Vendedor,
)

# ---------- Inlines / Admins auxiliares ----------


@admin.register(FrontPermission)
class FrontPermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "name")
    search_fields = ("codename", "name")
    ordering = ("codename",)


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = "__all__"


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    form = RoleForm
    list_display = ("name", "permissions_count")
    search_fields = ("name", "description", "permissions__codename")
    filter_horizontal = ("permissions",)
    ordering = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("permissions")

    def permissions_count(self, obj):
        return obj.permissions.count()

    permissions_count.short_description = "Qtd. permissões"


class LojaRoleInline(admin.TabularInline):
    model = UserRole
    extra = 0
    autocomplete_fields = ("user", "role")
    fields = ("user", "role")
    verbose_name = "Papel atribuído a usuário nesta loja"
    verbose_name_plural = "Papéis por usuário nesta loja"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "role")


class LojaFrontPermInline(admin.TabularInline):
    model = UserFrontPermission
    extra = 0
    autocomplete_fields = ("user", "permission")
    fields = ("user", "permission")
    verbose_name = "Permissão direta para usuário nesta loja"
    verbose_name_plural = "Permissões diretas por usuário nesta loja"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "permission")


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 0
    autocomplete_fields = ("role", "loja")
    fields = ("role", "loja")
    show_change_link = True
    verbose_name = "Papel do usuário"
    verbose_name_plural = "Papéis do usuário"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("role", "loja")


class UserFrontPermissionInline(admin.TabularInline):
    model = UserFrontPermission
    extra = 0
    autocomplete_fields = ("permission", "loja")
    fields = ("permission", "loja")
    show_change_link = True
    verbose_name = "Permissão direta (front)"
    verbose_name_plural = "Permissões diretas (front)"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("permission", "loja")


class OwnedLojaInline(admin.TabularInline):
    """
    Lojas em que o usuário é dono (FK Loja.dono).
    A M2M "lojas" (colaboradores) continua editável no formulário do usuário.
    """

    model = Loja
    fk_name = "dono"
    extra = 0
    fields = ("nome","data_criacao")
    readonly_fields = ("data_criacao",)
    show_change_link = True


# ---------- ModelAdmins básicos ----------


@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ("user", "nome_loja", "data_cadastro")
    search_fields = (
        "user__username",
        "user__email",
        "nome_loja__nome",  # campo correto no FK
    )
    autocomplete_fields = ("user", "nome_loja")
    ordering = ("-id",)
    date_hierarchy = "data_cadastro"


# ---------- UserAdmin ----------


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User

    list_display = (
        "username",
        "email",
        "display_name",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
    )
    search_fields = ("username", "email", "display_name", "first_name", "last_name")
    ordering = ("id",)

    # inlines
    inlines = [OwnedLojaInline, UserRoleInline, UserFrontPermissionInline]

    # M2M helpers
    filter_horizontal = ("groups", "user_permissions", "lojas")

    # campos somente leitura
    readonly_fields = ("public_id", "last_login", "date_joined")

    fieldsets = (
        (_("Identificação"), {"fields": ("public_id", "username", "password")}),
        (
            _("Informações pessoais"),
            {"fields": ("first_name", "last_name", "display_name", "email")},
        ),
        (
            _("Permissões"),
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
        (_("Datas importantes"), {"fields": ("last_login", "date_joined")}),
    )

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

    # --------- Ações em lote para aplicar/remover temas do FRONT ---------
    actions = ["remover_tema"]

    def get_actions(self, request):
        """
        Gera ações dinâmicas para cada Theme ativo.
        Usa closure por-theme com nome e descrição únicos.
        """
        actions = super().get_actions(request)

        # cria uma action por Theme ativo
        return actions


@admin.register(Loja)
class LojaAdmin(admin.ModelAdmin):
    list_display = ("nome", "dono", "data_criacao")
    list_filter = ("data_criacao",)
    search_fields = ("nome", "descricao", "dono__username", "dono__email")
    inlines = [LojaRoleInline, LojaFrontPermInline]
    autocomplete_fields = ("dono",)
    ordering = ("-id",)
    date_hierarchy = "data_criacao"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("dono",)
