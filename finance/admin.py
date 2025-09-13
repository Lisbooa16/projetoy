from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from finance.models import ContaPagar, ContaReceber, ParcelaReceber, Pessoa


class ParcelaReceberInline(admin.TabularInline):
    model = ParcelaReceber
    extra = 0
    fields = ("numero", "vencimento", "valor", "pago_em", "valor_pago")
    readonly_fields = ()
    show_change_link = True
    ordering = ("numero",)


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ("nome", "documento")
    search_fields = ("nome", "documento")
    ordering = ("nome",)


@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    inlines = [ParcelaReceberInline]
    list_display = (
        "descricao",
        "sacado",
        "valor_total",
        "emitida_em",
        "status",
        "venda",
    )
    list_filter = ("status", ("emitida_em", admin.DateFieldListFilter))
    search_fields = ("descricao", "sacado__nome", "sacado__documento", "venda__numero")
    autocomplete_fields = ("sacado", "venda")
    date_hierarchy = "emitida_em"
    actions = ("quitar_parcelas_abertas",)

    @admin.action(description=_("Quitar todas as parcelas em aberto"))
    def quitar_parcelas_abertas(self, request, queryset):
        from django.utils import timezone

        ok = 0
        for conta in queryset.select_related("sacado").prefetch_related("parcelas"):
            alterou = False
            for p in conta.parcelas.all():
                if not p.pago_em:
                    p.pago_em = timezone.now().date()
                    p.valor_pago = p.valor
                    p.save(update_fields=["pago_em", "valor_pago"])
                    alterou = True
            if alterou:
                conta.status = "paga"
                conta.save(update_fields=["status"])
                ok += 1
        if ok:
            self.message_user(
                request, _(f"{ok} conta(s) quitada(s)."), level=messages.SUCCESS
            )


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ("descricao", "favorecido", "valor_total", "emitida_em", "status")
    list_filter = ("status", ("emitida_em", admin.DateFieldListFilter))
    search_fields = ("descricao", "favorecido__nome", "favorecido__documento")
    autocomplete_fields = ("favorecido",)
    date_hierarchy = "emitida_em"
