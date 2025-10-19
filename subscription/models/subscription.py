from datetime import date, timedelta

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from custom_auth.models import Loja, User, Vendedor
from subscription.models.bills import Bills


class Subscription(models.Model):
    loja_responsavel = models.OneToOneField(
        Loja, on_delete=models.PROTECT, related_name="subscriptions_loja", unique=True
    )
    user = models.ManyToManyField(Vendedor, related_name="subscriptions")
    is_active = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    valido_ate = models.DateField(null=True, blank=True)
    pay = models.BooleanField(default=False)
    recurrence = models.BooleanField(default=False)

    @classmethod
    def user_has_active_subscription(cls, user):
        return cls.objects.filter(user=user, is_active=True).exists()

    def activate(self):
        """Ativa a assinatura e define validade para +30 dias."""
        self.is_active = True
        self.valido_ate = date.today() + timedelta(days=30)
        self.save(update_fields=["is_active", "valido_ate"])

    def deactivate(self):
        """Desativa e zera validade."""
        self.is_active = False
        self.valido_ate = None
        self.save(update_fields=["is_active", "valido_ate"])

    def reset_valid_until(self, days=30):
        """Redefine validade para +N dias a partir de hoje."""
        self.valido_ate = date.today() + timedelta(days=days)
        self.save(update_fields=["valido_ate"])

    def update_date_new_renew(self):
        """Estende a validade atual em +30 dias."""
        if self.valido_ate:
            self.valido_ate = self.valido_ate + timedelta(days=30)
            self.save(update_fields=["valido_ate"])

    def __str__(self):
        return f"Subscription({self.user}) - {'Ativa' if self.is_active else 'Inativa'}"


# ===========================================
# SIGNAL — cria fatura e ativa assinatura
# ===========================================
@receiver(
    post_save, sender=Subscription, dispatch_uid="reset_valid_date_and_create_bill"
)
def reset_valid_date_and_create_bill(sender, instance, created, **kwargs):
    """
    Quando uma Subscription é criada:
    - Ativa e define validade para +30 dias
    - Cria uma Bill pendente vinculada
    """
    if created:
        # Ativa e define validade
        instance.is_active = True
        instance.valido_ate = date.today() + timedelta(days=30)
        instance.save(update_fields=["is_active", "valido_ate"])

        # Cria a fatura pendente
        Bills.objects.create(
            sub=instance,
            status=Bills.Status.PENDING,
            created_at=instance.created_at,
        )
