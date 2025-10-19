from django.db import models
from django.utils import timezone

from custom_auth.models import Loja, User
from mail.utils import notificar_usuario


class TypeProduct(models.Model):
    type_product = models.CharField(max_length=255, verbose_name="Tipo de Produto")

    def __str__(self):
        return self.type_product


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nome")
    type_product = models.ForeignKey(
        TypeProduct, on_delete=models.PROTECT, verbose_name="Tipo de Produto"
    )
    store = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Loja",
    )

    def __str__(self):
        return self.name


class PriceProduct(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="prices"
    )
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name="Preço")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - R$ {self.price}"


class SaleHistory(models.Model):
    sales_by = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name="Vendido por"
    )
    product = models.ForeignKey(
        "Product", on_delete=models.PROTECT, verbose_name="Produto"
    )
    payment_method = models.ForeignKey(
        "PaymentMethod", on_delete=models.PROTECT, verbose_name="Forma de Pagamento"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data da Venda")

    def __str__(self):
        return f"{self.product.name} - {self.payment_method} - {self.sales_by}"

    def notify_sale(self):
        """Notifica dono da loja e o vendedor da venda."""

        # 🏬 dono da loja
        store_owner = getattr(self.product.store, "owner", None)

        # 🧑 vendedor (quem fez a venda)
        seller = self.sales_by

        # 🔹 mensagem genérica
        subject = f"Nova venda registrada — {self.product.name}"
        message = (
            f"💰 *Nova venda realizada!*\n\n"
            f"Produto: {self.product.name}\n"
            f"Quantidade: {self.quantity}\n"
            f"Forma de pagamento: {self.payment_method}\n"
            f"Data: {timezone.localtime(self.created_at).strftime('%d/%m/%Y %H:%M')}\n"
        )

        recipients = [seller]
        if store_owner and store_owner != seller:
            recipients.append(store_owner)

        # Envia mensagens internas
        notificar_usuario(
            recipients,
            subject=subject,
            message=message,
        )


class PaymentMethod(models.Model):
    class PaymentChoices(models.TextChoices):
        CREDIT = "credit", "Cartão de Crédito"
        DEBIT = "debit", "Cartão de Débito"
        PIX = "pix", "Pix"
        CASH = "cash", "Dinheiro"
        TRANSFER = "transfer", "Transferência Bancária"

    method_payment = models.CharField(
        max_length=20,
        choices=PaymentChoices.choices,  # type: ignore[attr-defined]
        verbose_name="Método de Pagamento",
    )
    active = models.BooleanField(default=True, verbose_name="Ativo")

    def __str__(self):
        return self.get_method_payment_display()
