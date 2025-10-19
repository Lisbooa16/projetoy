from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from custom_auth.models import Loja, User, Vendedor
from mail.models.mailbox import Message, MessageThread


class ComposeForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Destinatário",
        required=True,
    )
    subject = forms.CharField(label="Assunto", max_length=255)
    body = forms.CharField(label="Mensagem", widget=forms.Textarea(attrs={"rows": 4}))

    class Meta:
        model = Message
        fields = ["recipient", "subject", "body"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        # 🔹 agora verifica ManyToMany
        vendedor = (
            Vendedor.objects.filter(user=self.user).select_related("nome_loja").first()
        )

        if vendedor and vendedor.nome_loja:
            # 🔹 Pega todos os vendedores da mesma loja
            vendedores_mesma_loja = Vendedor.objects.filter(
                nome_loja=vendedor.nome_loja
            )

            # 🔹 Extrai apenas os usuários desses vendedores
            usuarios_mesma_loja = User.objects.filter(
                id__in=vendedores_mesma_loja.values_list("user_id", flat=True)
            ).exclude(id=self.user.id)

            self.fields["recipient"].queryset = usuarios_mesma_loja
        else:
            self.fields["recipient"].queryset = User.objects.none()

    def clean_recipient(self):
        recipient = self.cleaned_data["recipient"]

        # 🔹 Busca o vendedor do usuário logado
        vendedor_origem = (
            Vendedor.objects.filter(user=self.user).select_related("nome_loja").first()
        )

        # 🔹 Busca o vendedor do destinatário
        vendedor_destino = (
            Vendedor.objects.filter(user=recipient).select_related("nome_loja").first()
        )

        # 🔒 Valida se ambos têm loja e são da mesma
        if not vendedor_origem or not vendedor_destino:
            raise ValidationError(
                "Ambos os usuários precisam estar vinculados a uma loja para enviar mensagens."
            )

        if vendedor_origem.nome_loja != vendedor_destino.nome_loja:
            raise ValidationError(
                "Você só pode enviar mensagens para usuários da mesma loja."
            )

        return recipient

    def save(self, commit=True):
        recipient = self.cleaned_data["recipient"]
        subject = self.cleaned_data["subject"]
        body = self.cleaned_data["body"]

        # 🔹 cria (ou reutiliza) thread
        thread, _ = MessageThread.objects.get_or_create(subject=subject)
        thread.participants.set([self.user, recipient])

        # 🔹 cria mensagem
        msg = Message.objects.create(
            thread=thread,
            sender=self.user,
            recipient=recipient,
            body=body,
        )

        return msg


class ReplyForm(forms.ModelForm):
    """
    Responder dentro da thread existente.
    """

    class Meta:
        model = Message
        fields = ["body"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.thread = kwargs.pop("thread")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        # Destinatários = todos participantes menos o remetente atual
        recipients = self.thread.participants.exclude(id=self.user.id)
        # para DM, pega o primeiro destinatário
        recipient = recipients.first()

        msg = Message.objects.create(
            thread=self.thread,
            sender=self.user,
            recipient=recipient,
            body=self.cleaned_data["body"],
        )
        return msg
