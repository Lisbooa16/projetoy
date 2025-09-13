# inventory/signals.py
from __future__ import annotations

from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from inventory.models.inventory import Estoque, MovimentoEstoque


@receiver(post_save, sender=MovimentoEstoque)
def atualizar_estoque_apos_movimento(
    sender, instance: MovimentoEstoque, created, **kwargs
):
    if not created:
        return
    mov = instance
    estoque, _ = Estoque.objects.select_for_update().get_or_create(produto=mov.produto)

    if mov.tipo == MovimentoEstoque.Tipo.ENTRADA:
        # custo médio ponderado
        qtd_atual = Decimal(estoque.quantidade)
        custo_atual = Decimal(estoque.custo_medio)
        qtd_nova = Decimal(mov.quantidade)
        custo_novo = Decimal(mov.custo_unitario or 0)

        total_ant = qtd_atual * custo_atual
        total_novo = qtd_nova * custo_novo
        soma_qtd = qtd_atual + qtd_nova

        if soma_qtd > 0:
            estoque.custo_medio = ((total_ant + total_novo) / soma_qtd).quantize(
                Decimal("0.01")
            )
        estoque.quantidade = int(soma_qtd)
        estoque.save(update_fields=["quantidade", "custo_medio"])

    elif mov.tipo == MovimentoEstoque.Tipo.SAIDA:
        estoque.quantidade = int(Decimal(estoque.quantidade) - Decimal(mov.quantidade))
        if estoque.quantidade < 0:
            estoque.quantidade = 0
        estoque.save(update_fields=["quantidade"])

    elif mov.tipo == MovimentoEstoque.Tipo.AJUSTE:
        # Convenção: quantidade positiva => aumenta, negativa => diminui
        nova_qtd = Decimal(estoque.quantidade) + Decimal(mov.quantidade)
        estoque.quantidade = int(max(nova_qtd, 0))
        if mov.custo_unitario is not None and mov.quantidade > 0:
            # ajuste positivo com custo declarado -> recalcula custo médio
            qtd_atual = Decimal(estoque.quantidade)
            custo_atual = Decimal(estoque.custo_medio)
            qtd_nova = Decimal(mov.quantidade)
            custo_novo = Decimal(mov.custo_unitario or 0)
            total_ant = qtd_atual * custo_atual
            total_novo = qtd_nova * custo_novo
            soma_qtd = qtd_atual + qtd_nova
            if soma_qtd > 0:
                estoque.custo_medio = ((total_ant + total_novo) / soma_qtd).quantize(
                    Decimal("0.01")
                )
        estoque.save(update_fields=["quantidade", "custo_medio"])
