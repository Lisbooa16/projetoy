from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from .models import LancamentoComissao, RegraComissao


@admin.register(RegraComissao)
class RegraComissaoAdmin(admin.ModelAdmin):
    list_display = (
        "vendedor",
        "categoria",
        "produto",
        "percentual",
        "base_calculo",
        "ativo",
        "prioridade",
    )
    list_filter = ("ativo", "base_calculo")
    search_fields = (
        "vendedor__username",
        "vendedor__first_name",
        "vendedor__last_name",
        "categoria__nome",
        "produto__nome",
    )
    autocomplete_fields = ("vendedor", "categoria", "produto")
    ordering = ("prioridade", "vendedor")


@admin.register(LancamentoComissao)
class LancamentoComissaoAdmin(admin.ModelAdmin):
    list_display = ("venda", "item", "vendedor", "valor", "status", "criado_em")
    list_filter = ("status", ("criado_em", admin.DateFieldListFilter))
    search_fields = (
        "venda__numero",
        "vendedor__username",
        "vendedor__first_name",
        "vendedor__last_name",
    )
    autocomplete_fields = ("venda", "item", "vendedor")
    date_hierarchy = "criado_em"
    actions = ("marcar_paga",)

    @admin.action(description=_("Marcar lançamentos selecionados como PAGOS"))
    def marcar_paga(self, request, queryset):
        updated = queryset.update(status="paga")
        self.message_user(
            request,
            _(f"{updated} lançamento(s) marcado(s) como pago(s)."),
            level=messages.SUCCESS,
        )
