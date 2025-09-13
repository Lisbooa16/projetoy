from django.contrib import admin
from django.db.models import F, Sum

from inventory.models.inventory import Estoque, MovimentoEstoque


@admin.register(Estoque)
class EstoqueAdmin(admin.ModelAdmin):
    list_display = ("produto", "quantidade", "custo_medio", "valor_total")
    search_fields = ("produto__nome", "produto__codigo_barras")
    autocomplete_fields = ("produto",)
    readonly_fields = ("quantidade", "custo_medio")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("produto")

    def valor_total(self, obj):
        return obj.quantidade * obj.custo_medio

    valor_total.short_description = "Valor total (custo)"


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = (
        "produto",
        "tipo",
        "quantidade",
        "custo_unitario",
        "motivo",
        "referencia",
        "criado_em",
    )
    list_filter = ("tipo", ("criado_em", admin.DateFieldListFilter))
    search_fields = ("produto__nome", "referencia", "motivo")
    autocomplete_fields = ("produto",)
    date_hierarchy = "criado_em"
    ordering = ("-criado_em",)
