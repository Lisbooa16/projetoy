from django import forms
from django.contrib import admin

from custom_auth.models import Vendedor

from .models import Subscription


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = "__all__"

    def clean_user(self):
        users = self.cleaned_data.get("user")
        loja = self.cleaned_data.get("loja_responsavel")

        # Garante consistência na validação (sem quebrar o admin)
        if loja and users.exists():
            for u in users:
                if u.nome_loja != loja:
                    raise forms.ValidationError(
                        f"O vendedor {u.nome} não pertence à loja {loja.nome}."
                    )
        return users

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        loja_id = None
        if self.data.get("loja_responsavel"):
            loja_id = self.data.get("loja_responsavel")
        elif self.instance and self.instance.loja_responsavel_id:
            loja_id = self.instance.loja_responsavel_id

        # IDs já selecionados no formulário
        selected_ids = []
        if self.data.getlist("user"):
            selected_ids = self.data.getlist("user")
        elif self.instance.pk:
            selected_ids = self.instance.user.values_list("pk", flat=True)

        # Queryset base
        if loja_id:
            qs = Vendedor.objects.filter(nome_loja_id=loja_id)
        else:
            qs = Vendedor.objects.none()

        # 🔥 Mantenha sempre os selecionados no queryset
        if selected_ids:
            qs = qs | Vendedor.objects.filter(pk__in=selected_ids)

        self.fields["user"].queryset = qs.distinct()
