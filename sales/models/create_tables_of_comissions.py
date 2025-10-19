from decimal import Decimal

from django.db import models

from custom_auth.models import User, Vendedor
from sales.models.sales_of_products import PaymentMethod, Product, SaleHistory


class Commission(models.Model):
    """
    Representa uma comissão paga (ou a pagar) ao vendedor por uma venda.
    """

    sale = models.ForeignKey(
        SaleHistory,
        on_delete=models.CASCADE,
        related_name="commissions",
        verbose_name="Venda",
    )
    seller = models.ForeignKey(
        Vendedor,
        on_delete=models.PROTECT,
        related_name="commissions",
        verbose_name="Vendedor",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="commissions",
        verbose_name="Produto",
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Forma de Pagamento",
    )

    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Percentual de Comissão (%)",
        help_text="Exemplo: 5.00 para 5%.",
    )
    commission_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Valor da Comissão (R$)",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de criação")
    paid = models.BooleanField(default=False, verbose_name="Comissão paga?")

    class Meta:
        verbose_name = "Comissão"
        verbose_name_plural = "Comissões"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.seller} - {self.product.name} ({self.commission_rate}%)"

    def calculate_commission(self, sale_price: Decimal):
        """Calcula automaticamente o valor da comissão baseado no preço da venda."""
        self.commission_value = (sale_price * self.commission_rate) / Decimal("100")
        return self.commission_value
