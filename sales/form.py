from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from custom_auth.models import Vendedor

from .models import Commission, PaymentMethod, PriceProduct, Product, SaleHistory, Stock


class SaleForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Produto",
        required=True,
    )
    quantity = forms.IntegerField(min_value=1, initial=1, label="Quantidade")
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.all(),
        label="Forma de pagamento",
        required=True,
    )

    class Meta:
        model = SaleHistory
        fields = ["sales_by"]

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get("product")
        quantity = cleaned.get("quantity")

        if product and quantity:
            stock = getattr(product, "stock", None)
            if not stock:
                raise forms.ValidationError(
                    f"O produto {product} não possui estoque cadastrado."
                )
            if stock.quantity < quantity:
                raise forms.ValidationError(
                    f"Estoque insuficiente: {stock.quantity} disponíveis."
                )
        return cleaned

    def save(self, commit=True):
        with transaction.atomic():
            sale = super().save(commit=False)
            sale.save()

            # Pega preço atual
            price_obj = sale.product.prices.order_by("-updated_at").first()
            price = price_obj.price if price_obj else Decimal("0.00")

            vendedor = Vendedor.objects.get(user=sale.sales_by)
            Commission.objects.create(
                sale=sale,
                seller=vendedor,
                product=sale.product,
                payment_method=sale.payment_method,
                commission_rate=Decimal("5.00"),
                commission_value=(price * sale.quantity * Decimal("0.05")),
            )

            return sale
