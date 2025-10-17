from django.contrib import admin
from django.utils.html import format_html
from datetime import date, timedelta

from .models import Subscription
from subscription.models.bills import Bills


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "is_active",
        "valido_ate",
        "pay",
        "recurrence",
        "status_color",
        "created_at",
    )
    list_filter = ("is_active", "pay", "recurrence", "created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    actions = ["ativar_assinaturas", "desativar_assinaturas", "renovar_assinaturas"]

    def status_color(self, obj):
        """Mostra uma bolinha verde/vermelha conforme status."""
        color = "#4CAF50" if obj.is_active else "#F44336"
        label = "Ativa" if obj.is_active else "Inativa"
        return format_html(f'<b style="color:{color}">●</b> {label}')
    status_color.short_description = "Status"

    # ===============================
    # AÇÕES PERSONALIZADAS
    # ===============================
    @admin.action(description="Ativar assinaturas selecionadas")
    def ativar_assinaturas(self, request, queryset):
        for sub in queryset:
            sub.activate()
        self.message_user(request, f"{queryset.count()} assinatura(s) ativada(s).")

    @admin.action(description="Desativar assinaturas selecionadas")
    def desativar_assinaturas(self, request, queryset):
        for sub in queryset:
            sub.deactivate()
        self.message_user(request, f"{queryset.count()} assinatura(s) desativada(s).")

    @admin.action(description="Renovar assinaturas (+30 dias)")
    def renovar_assinaturas(self, request, queryset):
        renovadas = 0
        for sub in queryset:
            sub.update_date_new_renew()
            # Cria uma nova fatura a cada renovação
            Bills.objects.create(
                sub=sub,
                status=Bills.Status.PENDING,
                created_at=date.today(),
            )
            renovadas += 1
        self.message_user(request, f"{renovadas} assinatura(s) renovada(s) com sucesso.")
