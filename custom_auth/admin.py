from __future__ import annotations

from django import forms
from django.apps import apps
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

# Importa tudo do próprio app (evita caminho errado tipo custom_auth.models.user)
from .models import (
    FrontPermission,
    GroupObjectPermission,
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
    fields = ("nome", "data_criacao")
    readonly_fields = ("data_criacao",)
    show_change_link = True


# ---------- ModelAdmins básicos ----------


@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "nome_loja", "user", "data_cadastro")
    search_fields = ("nome", "email", "nome_loja__nome")
    list_filter = ("nome_loja", "data_cadastro")
    readonly_fields = ("user", "data_cadastro")
    ordering = ("-data_cadastro",)
    date_hierarchy = "data_cadastro"
    autocomplete_fields = ("nome_loja",)

    fieldsets = (
        (
            "Informações do Vendedor",
            {
                "fields": ("nome", "email", "nome_loja", "descricao_loja"),
            },
        ),
        (
            "Sistema",
            {
                "fields": ("user", "data_cadastro"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        Apenas chama o save() normal — o próprio modelo
        cuida da criação automática do User e envio do e-mail.
        """
        super().save_model(request, obj, form, change)


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
    filter_horizontal = (
        "groups",
        "user_permissions",
        "lojas",
        "allowed_actions",
    )

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
                    "allowed_actions",
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
        return qs.select_related(
            "dono",
        )


# -------------------------------------------------
# 🔹 Helper: retorna todos os models registrados
# -------------------------------------------------
def get_all_model_choices():
    """Retorna todos os models registrados (app.model)."""
    choices = []
    for model in apps.get_models():
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        verbose = f"{app_label}.{model.__name__}"
        key = f"{app_label}.{model_name}"
        choices.append((key, verbose))
    return sorted(choices, key=lambda x: x[1])


# -------------------------------------------------
# 🔹 Formulário customizado do admin
# -------------------------------------------------
class GroupObjectPermissionForm(forms.ModelForm):
    model_names = forms.MultipleChoiceField(
        label="Modelos",
        choices=get_all_model_choices(),
        widget=admin.widgets.FilteredSelectMultiple("modelos", is_stacked=False),
    )

    users = forms.ModelMultipleChoiceField(
        queryset=None,
        label="Usuários",
        widget=admin.widgets.FilteredSelectMultiple("usuários", is_stacked=False),
    )

    class Meta:
        model = GroupObjectPermission
        fields = ["group", "users", "model_names", "action"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model

        # 🔹 Atualiza dinamicamente o queryset de usuários
        self.fields["users"].queryset = get_user_model().objects.all()

        # 🔹 Preenche initial de model_names ao editar
        if self.instance.pk:
            self.fields["model_names"].initial = self.instance.model_names

    def clean_model_names(self):
        """Converte o campo MultipleChoiceField em lista JSON compatível."""
        return list(self.cleaned_data["model_names"])

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.model_names = list(self.cleaned_data["model_names"])
        if commit:
            instance.save()
            self.save_m2m()
        return instance


# -------------------------------------------------
# 🔹 Admin personalizado
# -------------------------------------------------
@admin.register(GroupObjectPermission)
class GroupObjectPermissionAdmin(admin.ModelAdmin):
    form = GroupObjectPermissionForm
    list_display = ("group", "action", "display_models", "user_count")
    list_filter = ("group", "action")
    search_fields = ("group__name",)
    autocomplete_fields = ("group",)

    def display_models(self, obj):
        return ", ".join(obj.model_names or [])

    display_models.short_description = "Modelos"

    def user_count(self, obj):
        return obj.users.count()

    user_count.short_description = "Usuários"

    # 🔒 Apenas superusuários podem manipular essas permissões
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_model_perms(self, request):
        """Oculta o modelo no menu do admin para não-superusers."""
        if not request.user.is_superuser:
            return {}
        return super().get_model_perms(request)
