from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class MessageThread(models.Model):
    """
    Uma conversa (thread) entre 2+ usuários.
    """

    subject = models.CharField(max_length=255, verbose_name="Assunto")
    participants = models.ManyToManyField(User, related_name="message_threads")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject

    def last_message(self):
        return self.messages.order_by("-sent_at").first()

    def unread_count_for(self, user):
        return self.messages.filter(recipient=user, is_read=False).count()


class Message(models.Model):
    """
    Uma mensagem individual dentro de uma thread.
    """

    thread = models.ForeignKey(
        MessageThread, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="messages_sent",
        null=True,  # ✅ permite mensagens do sistema
        blank=True,
    )
    recipient = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="messages_received"
    )
    body = models.TextField(verbose_name="Mensagem")
    sent_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["sent_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["thread", "sent_at"]),
        ]

    def __str__(self):
        return f"{self.sender} → {self.recipient} ({self.sent_at:%d/%m %H:%M})"
