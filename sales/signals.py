from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.utils import timezone

from mail.utils import notificar_usuario

from .models import PaymentMethod, Product, SaleHistory, Stock


def create_default_payment_methods():
    DEFAULT_METHODS = [
        "Cartão de Crédito",
        "Cartão de Débito",
        "Pix",
        "Dinheiro",
        "Transferência Bancária",
    ]

    for name in DEFAULT_METHODS:
        PaymentMethod.objects.get_or_create(method_payment=name)


@receiver(post_save, sender=SaleHistory)
def notificar_venda_e_estoque(sender, instance: SaleHistory, created, **kwargs):
    """
    Dispara notificações após uma venda:
    - Avisa o vendedor e o dono da loja.
    - Atualiza o estoque e notifica se estiver baixo.
    """
    if not created:
        return  # evita rodar em updates

    product = instance.product
    stock = getattr(product, "stock", None)
    if not stock:
        print(f"[⚠️] Produto '{product}' não possui registro de estoque.")
        return

    # === 1️⃣ Diminui o estoque com segurança
    try:
        stock.decrease(instance.quantity)
    except ValueError as e:
        print(f"[❌] Estoque insuficiente para '{product.name}': {e}")
        return
    except Exception as e:
        print(f"[!] Erro inesperado ao atualizar estoque: {e}")
        return

    # === 2️⃣ Notifica venda
    store_owner = getattr(product.store, "owner", None)
    seller = instance.sales_by

    subject = f"💰 Nova venda registrada — {product.name}"
    message = (
        f"💵 *Nova venda realizada!*\n\n"
        f"Produto: {product.name}\n"
        f"Quantidade vendida: {instance.quantity}\n"
        f"Forma de pagamento: {instance.payment_method}\n"
        f"Data: {timezone.localtime(instance.created_at).strftime('%d/%m/%Y %H:%M')}\n"
    )

    # 👥 destinatários: vendedor + dono da loja
    recipients = [seller]
    if store_owner and store_owner != seller:
        recipients.append(store_owner)

    try:
        notificar_usuario(recipients, subject=subject, message=message)
        print(
            f"[✅] Notificação de venda enviada para {[u.username for u in recipients]}"
        )
    except Exception as e:
        print(f"[⚠️] Falha ao notificar venda: {e}")

    # === 3️⃣ Verifica estoque baixo (após diminuir)
    LIMITE = getattr(stock, "LOW_STOCK_THRESHOLD", 5)

    if stock.quantity <= LIMITE:
        try:
            subject = f"⚠️ Estoque baixo — {product.name}"
            message = (
                f"O estoque do produto *{product.name}* está baixo.\n"
                f"Quantidade atual: {stock.quantity} unidade(s).\n"
                f"Reabasteça o estoque o quanto antes."
            )
            owner = Product.objects.filter(id=product.id).first()
            print(owner.store)
            if owner:
                print("to aq")
                try:
                    notificar_usuario(
                        owner.store.dono, subject=subject, message=message
                    )
                    print(
                        f"[⚠️] Estoque baixo notificado para {owner.store.dono.username}"
                    )
                except Exception as e:
                    print(f"[⚠️] Falha ao notificar estoque baixo: {e}")
        except Exception as e:
            print(f"1 {e}")
