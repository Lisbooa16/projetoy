from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from mail.models.mailbox import MessageThread, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "recipient", "body", "sent_at", "is_read")
    fields = ("sender", "recipient", "body", "sent_at", "is_read")
    can_delete = False


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ("subject", "created_at", "get_participants", "get_last_preview")
    search_fields = ("subject", "participants__username", "participants__email")
    inlines = [MessageInline]
    change_list_template = "admin/mail/message_thread/change_list.html"

    def changelist_view(self, request, extra_context=None):
        """
        Adiciona o botão '💬 Ver Caixa de Entrada' no topo do admin,
        redirecionando para a rota pública /messages/.
        """
        extra_context = extra_context or {}

        # gera a URL absoluta correta
        inbox_url = request.build_absolute_uri(reverse("mailbox:inbox"))
        extra_context["inbox_url"] = inbox_url

        # ✅ chama o changelist_view original (mantém app_label, breadcrumbs, filtros etc.)
        return super().changelist_view(request, extra_context=extra_context)

    def get_participants(self, obj):
        return ", ".join(sorted(u.username for u in obj.participants.all()))
    get_participants.short_description = "Participantes"

    def get_last_preview(self, obj):
        last = obj.last_message()
        if not last:
            return "-"
        txt = (last.body or "").strip().replace("\n", " ")
        return (txt[:60] + "…") if len(txt) > 60 else txt
    get_last_preview.short_description = "Última mensagem"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("thread", "sender", "recipient", "sent_at", "is_read")
    list_filter = ("is_read", "sent_at")
    search_fields = ("sender__username", "recipient__username", "body", "thread__subject")
