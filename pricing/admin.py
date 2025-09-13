from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from .models import RegraPreco, TabelaPreco


class RegraPrecoInline(admin.TabularInline):
    model = RegraPreco
    extra = 0
    autocomplete_fields = ("produto", "categoria")
    fields = (
        "produto",
        "categoria",
        "percentual_desconto",
        "preco_fixo",
        "data_inicio",
        "data_fim",
        "combinavel",
    )
    show_change_link = True


@admin.register(TabelaPreco)
class TabelaPrecoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "prioridade", "regras_count")
    list_filter = ("ativo",)
    search_fields = ("nome",)
    ordering = ("prioridade", "nome")
    inlines = [RegraPrecoInline]
    actions = ("ativar", "desativar")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("regras")

    def regras_count(self, obj):
        return obj.regras.count()

    regras_count.short_description = "Regras"

    @admin.action(description=_("Ativar tabelas selecionadas"))
    def ativar(self, request, queryset):
        updated = queryset.update(ativo=True)
        self.message_user(
            request, _(f"{updated} tabela(s) ativada(s)."), level=messages.SUCCESS
        )

    @admin.action(description=_("Desativar tabelas selecionadas"))
    def desativar(self, request, queryset):
        updated = queryset.update(ativo=False)
        self.message_user(
            request, _(f"{updated} tabela(s) desativada(s)."), level=messages.WARNING
        )


@admin.register(RegraPreco)
class RegraPrecoAdmin(admin.ModelAdmin):
    list_display = (
        "tabela",
        "produto",
        "categoria",
        "percentual_desconto",
        "preco_fixo",
        "data_inicio",
        "data_fim",
        "combinavel",
    )
    list_filter = (
        ("data_inicio", admin.DateFieldListFilter),
        ("data_fim", admin.DateFieldListFilter),
        "combinavel",
        "tabela",
    )
    search_fields = ("tabela__nome", "produto__nome", "categoria__nome")
    autocomplete_fields = ("tabela", "produto", "categoria")
    ordering = ("tabela__prioridade", "tabela__nome", "produto__nome")
