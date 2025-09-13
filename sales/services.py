# sales/services.py
from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from commissions.models import LancamentoComissao, RegraComissao
from finance.models import ContaReceber, ParcelaReceber, Pessoa
from inventory.models import Estoque, MovimentoEstoque
from pricing.services import get_preco
from products.models import Produto

from .models import ItemVenda, Venda


@transaction.atomic
def adicionar_item_com_precificacao(
    venda: Venda, produto: Produto, quantidade: int
) -> ItemVenda:
    """Adiciona item já com preço calculado por pricing/promos e congela preço."""
    preco = get_preco(produto=produto, dt=timezone.now())
    item = ItemVenda.objects.create(
        venda=venda,
        produto=produto,
        quantidade=quantidade,
        preco_unitario=preco,
        valor_desconto=Decimal("0.00"),
        custo_unitario=_custo_unitario_atual(produto),
    )
    venda.recalcular_totais()
    venda.save(update_fields=["subtotal", "total"])
    return item


def _custo_unitario_atual(produto: Produto) -> Decimal:
    """Consulta custo médio do registro de estoque; fallback 0.00."""
    try:
        return Decimal(produto.estoque_registro.custo_medio)
    except Exception:
        return Decimal("0.00")


def _gerar_saida_estoque(item: ItemVenda):
    """
    Gera MovimentoEstoque(SAIDA) e baixa a quantidade.
    Usa select_for_update no registro de estoque.
    """
    estoque, _ = Estoque.objects.select_for_update().get_or_create(produto=item.produto)
    if estoque.quantidade < item.quantidade:
        raise ValueError(
            f"Estoque insuficiente para {item.produto} (disp: {estoque.quantidade}, req: {item.quantidade})"
        )

    MovimentoEstoque.objects.create(
        produto=item.produto,
        tipo=MovimentoEstoque.Tipo.SAIDA,
        quantidade=item.quantidade,
        custo_unitario=estoque.custo_medio,
        motivo="Venda faturada",
        referencia=str(item.venda.numero),
    )
    # atualização do estoque ficará a cargo do signal post_save de MovimentoEstoque


def _criar_conta_receber(venda: Venda, parcelas: int = 1):
    """Cria Conta a Receber e parcelas iguais (simples)."""
    if not venda.cliente:
        # cria sacado generico se não houver cliente
        sacado, _ = Pessoa.objects.get_or_create(nome="Cliente PDV")
    else:
        sacado, _ = Pessoa.objects.get_or_create(
            nome=venda.cliente.nome,
            defaults={"documento": venda.cliente.documento or ""},
        )

    cr = ContaReceber.objects.create(
        venda=venda,
        sacado=sacado,
        descricao=f"Venda {venda.numero}",
        valor_total=venda.total,
        emitida_em=timezone.now().date(),
        status="aberta",
    )
    valor_parc = (venda.total / parcelas).quantize(Decimal("0.01"))
    for i in range(1, parcelas + 1):
        ParcelaReceber.objects.create(
            conta=cr,
            numero=i,
            vencimento=timezone.now().date(),  # ajuste: calcule conforme forma_pagamento
            valor=valor_parc,
        )
    return cr


def _melhor_regra_comissao(item: ItemVenda):
    """Seleciona a melhor regra por prioridade (menor valor)."""
    qs = RegraComissao.objects.filter(ativo=True).order_by("prioridade", "id")
    # match por vendedor
    qs = qs.filter(vendedor=item.venda.vendedor) | qs.filter(vendedor__isnull=True)
    # match por produto/categoria
    qs = (
        qs.filter(produto=item.produto)
        | qs.filter(categoria=item.produto.categoria)
        | qs.filter(produto__isnull=True, categoria__isnull=True)
    )
    return qs.first()


def _gerar_comissao_item(item: ItemVenda):
    regra = _melhor_regra_comissao(item)
    if not regra:
        return None

    if regra.base_calculo == "receita":
        base = item.preco_unitario * item.quantidade
    else:  # margem
        margem_unit = item.preco_unitario - (item.custo_unitario or Decimal("0.00"))
        base = margem_unit * item.quantidade

    valor = (base * (regra.percentual / Decimal("100"))).quantize(Decimal("0.01"))
    if valor <= 0:
        return None

    return LancamentoComissao.objects.create(
        venda=item.venda,
        item=item,
        vendedor=item.venda.vendedor,
        valor=valor,
        status="aberta",
    )


@transaction.atomic
def faturar_venda(venda_id: int, emitir_nfe: bool = False, parcelas: int = 1) -> Venda:
    """
    Faturação completa:
    - valida/fecha venda (se necessário)
    - baixa estoque (gera MovimentoEstoque SAIDA por item)
    - cria Conta a Receber (+ parcelas)
    - calcula/lança comissões
    - opcional: emite NFe (chama service)
    """
    venda = Venda.objects.select_for_update().get(id=venda_id)

    if not venda.itens.exists():
        raise ValueError("Venda sem itens.")
    if venda.status == Venda.Status.RASCUNHO:
        venda.fechar()

    # estoque (saídas)
    for item in venda.itens.select_related("produto"):
        _gerar_saida_estoque(item)

    # contas a receber
    _criar_conta_receber(venda, parcelas=parcelas)

    # comissões
    for item in venda.itens.all():
        _gerar_comissao_item(item)

    # marcar venda como faturada
    venda.status = Venda.Status.FATURADA
    venda.save(update_fields=["status"])

    # NFe (opcional)
    if emitir_nfe:
        try:
            from invoicing.services import emitir_nfe  # crie depois

            emitir_nfe(venda.id)
        except Exception:
            # não quebra a faturação; logue/monitore
            pass

    return venda
