from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from .models import NotaFiscal


@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    list_display = (
        "venda",
        "numero",
        "serie",
        "status",
        "chave",
        "protocolo",
        "criado_em",
    )
    list_filter = ("status", ("criado_em", admin.DateFieldListFilter))
    search_fields = ("venda__numero", "numero", "chave", "protocolo")
    autocomplete_fields = ("venda",)
    date_hierarchy = "criado_em"
    readonly_fields = ("xml_autorizado",)
    actions = ("emitir_nfe", "cancelar_nfe")

    @admin.action(description=_("Emitir NFe das selecionadas"))
    def emitir_nfe(self, request, queryset):
        # from invoicing.services import emitir_nfe
        ok, err = 0, 0
        for nfe in queryset.select_related("venda"):
            try:
                # emitir_nfe(nfe.venda_id)
                nfe.status = "autorizada"  # placeholder: ajuste quando integrar
                nfe.save(update_fields=["status"])
                ok += 1
            except Exception as e:
                err += 1
                self.message_user(
                    request,
                    f"Erro ao emitir NFe da venda {nfe.venda}: {e}",
                    level=messages.ERROR,
                )
        if ok:
            self.message_user(
                request, _(f"{ok} NFe(s) processada(s)."), level=messages.SUCCESS
            )

    @admin.action(description=_("Cancelar NFe das selecionadas"))
    def cancelar_nfe(self, request, queryset):
        # from invoicing.services import cancelar_nfe
        ok, err = 0, 0
        for nfe in queryset:
            try:
                # cancelar_nfe(nfe.id)
                nfe.status = "cancelada"  # placeholder
                nfe.save(update_fields=["status"])
                ok += 1
            except Exception as e:
                err += 1
                self.message_user(
                    request, f"Erro ao cancelar NFe {nfe.id}: {e}", level=messages.ERROR
                )
        if ok:
            self.message_user(
                request, _(f"{ok} NFe(s) cancelada(s)."), level=messages.SUCCESS
            )
