from decimal import Decimal

from django.db import models

from mail.utils import notificar_usuario
from sales.models.sales_of_products import Product


class Stock(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="stock",
        verbose_name="Produto",
    )
    quantity = models.PositiveIntegerField(
        default=0, verbose_name="Quantidade em estoque"
    )
    cost_price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Custo unitário (R$)",
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última atualização")
    LOW_STOCK_THRESHOLD = 5  # 🔸 define limite mínimo

    class Meta:
        verbose_name = "Estoque"
        verbose_name_plural = "Estoques"

    def __str__(self):
        return f"{self.product.name} - {self.quantity} unid."

    # 👇 Métodos auxiliares úteis
    def increase(self, amount: int):
        """Adiciona itens ao estoque."""
        self.quantity += amount
        self.save(update_fields=["quantity", "updated_at"])

    def decrease(self, amount: int):
        """Remove itens do estoque, sem deixar negativo."""
        if amount <= 0:
            raise ValueError("Quantidade inválida.")
        if amount > self.quantity:
            raise ValueError(
                f"Quantidade insuficiente em estoque. ({self.quantity} disponíveis)"
            )
        self.quantity -= amount
        self.save(update_fields=["quantity", "updated_at"])

    def notify_low_stock(self):
        """Notifica o dono da loja que o estoque está acabando."""
        store_owner = getattr(self.product.store, "owner", None)
        print("ta aq")
        if not store_owner:
            print("ta aq")
            return

        subject = f"⚠️ Estoque baixo — {self.product.name}"
        message = (
            f"O estoque do produto *{self.product.name}* está baixo.\n"
            f"Quantidade atual: {self.quantity} unidade(s).\n"
            f"Reabasteça o estoque o quanto antes."
        )

        notificar_usuario(
            store_owner,
            subject=subject,
            message=message,
        )
