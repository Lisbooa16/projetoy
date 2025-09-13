from decimal import Decimal

from django.contrib import admin, messages
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from .models import Cliente, FormaPagamento, ItemVenda, Venda

# -------- Inlines --------


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0
    autocomplete_fields = ("produto",)
    fields = (
        "produto",
        "quantidade",
        "preco_unitario",
        "valor_desconto",
        "custo_unitario",
    )
    readonly_fields = ()
    show_change_link = True


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "documento", "email", "telefone")
    search_fields = ("nome", "documento", "email", "telefone")
    ordering = ("nome",)


@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "exige_parcelamento")
    list_filter = ("exige_parcelamento",)
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    inlines = [ItemVendaInline]
    date_hierarchy = "criado_em"
    list_display = (
        "numero",
        "status",
        "cliente",
        "vendedor",
        "subtotal",
        "desconto_total",
        "acrescimo_total",
        "total",
        "criado_em",
    )
    list_filter = (
        "status",
        "forma_pagamento",
        ("criado_em", admin.DateFieldListFilter),
    )
    search_fields = (
        "numero",
        "cliente__nome",
        "cliente__documento",
        "vendedor__username",
        "vendedor__first_name",
        "vendedor__last_name",
    )
    autocomplete_fields = ("cliente", "vendedor", "forma_pagamento")
    readonly_fields = ()
    actions = ("acao_fechar", "acao_faturar")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "cliente", "vendedor", "forma_pagamento"
        ).prefetch_related(Prefetch("itens"))

    @admin.action(description=_("Fechar vendas selecionadas (Rascunho → Aberta)"))
    def acao_fechar(self, request, queryset):
        ok = 0
        for venda in queryset:
            try:
                if venda.status == venda.Status.RASCUNHO:
                    venda.fechar()
                    ok += 1
            except Exception as e:
                self.message_user(
                    request, f"Erro ao fechar {venda}: {e}", level=messages.ERROR
                )
        if ok:
            self.message_user(
                request, _(f"{ok} venda(s) fechada(s)."), level=messages.SUCCESS
            )

    @admin.action(
        description=_(
            "Faturar vendas selecionadas (gera saída estoque, contas a receber, etc.)"
        )
    )
    def acao_faturar(self, request, queryset):
        # Substitua pelo seu service real:
        # from sales.services import faturar_venda
        ok, err = 0, 0
        for venda in queryset:
            try:
                # faturar_venda(venda.id, emitir_nfe=False)
                venda.status = venda.Status.FATURADA
                venda.save(update_fields=["status"])
                ok += 1
            except Exception as e:
                err += 1
                self.message_user(
                    request, f"Erro ao faturar {venda}: {e}", level=messages.ERROR
                )
        if ok:
            self.message_user(
                request, _(f"{ok} venda(s) faturada(s)."), level=messages.SUCCESS
            )


@admin.register(ItemVenda)
class ItemVendaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "venda",
        "produto",
        "quantidade",
        "preco_unitario",
        "valor_desconto",
    )
    search_fields = (
        "venda__numero",
        "produto__nome",
        "produto__codigo_barras",
    )
    autocomplete_fields = ("venda", "produto")
    list_select_related = ("venda", "produto")
