# pricing/services.py
from __future__ import annotations

from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from products.models import Produto, Promocao

from .models import RegraPreco, TabelaPreco


def _melhor_preco_por_regras(produto: Produto, dt=None) -> Decimal | None:
    """
    Aplica Tabelas/ Regras ativas por prioridade.
    Estratégia: para cada tabela ativa (ordenada por prioridade asc),
    procura regra por produto; se não achar, por categoria; aplica:
      - se houver preco_fixo, usa e (se combinavel=False) para
      - se percentual_desconto, aplica sobre o preço corrente acumulado
    """
    dt = dt or timezone.now()
    preco = Decimal(produto.preco)  # preço base do produto
    aplicou = False

    tabelas = (
        TabelaPreco.objects.filter(ativo=True)
        .order_by("prioridade", "id")
        .prefetch_related("regras")
    )

    for tabela in tabelas:
        # Regras ativas por produto/categoria
        regras = [
            r
            for r in tabela.regras.all()
            if r.ativa(dt)
            and (
                (r.produto_id == produto.id) or (r.categoria_id == produto.categoria_id)
            )
        ]

        for r in regras:
            if r.preco_fixo is not None:
                preco = Decimal(r.preco_fixo)
                aplicou = True
                if not r.combinavel:
                    return preco  # trava aqui
            if r.percentual_desconto and r.percentual_desconto > 0:
                desconto = (Decimal(r.percentual_desconto) / Decimal("100")) * preco
                preco = (preco - desconto).quantize(Decimal("0.01"))
                aplicou = True
                if not r.combinavel:
                    return preco

    return preco if aplicou else None


def _aplica_promocoes(produto: Produto, preco_atual: Decimal, dt=None) -> Decimal:
    """Aplica a MAIOR promoção ativa entre as vinculadas ao produto (desconto percentual)."""
    dt = dt or timezone.now()
    promocoes_ativas = Promocao.objects.filter(
        produtos=produto,
        data_inicio__lte=dt,
        data_fim__gte=dt,
    ).values_list("desconto_percentual", flat=True)

    if not promocoes_ativas:
        return preco_atual

    maior = max(promocoes_ativas) or Decimal("0")
    if maior <= 0:
        return preco_atual
    desconto = (Decimal(maior) / Decimal("100")) * preco_atual
    return (preco_atual - desconto).quantize(Decimal("0.01"))


def get_preco(produto: Produto, cliente=None, dt=None) -> Decimal:
    """
    Retorna o preço efetivo agora considerando:
      1) Tabelas/Regras (por prioridade)
      2) Promoções (maior desconto)
    """
    dt = dt or timezone.now()
    base = Decimal(produto.preco)
    preco_regras = _melhor_preco_por_regras(produto, dt) or base
    preco_final = _aplica_promocoes(produto, preco_regras, dt)
    return preco_final.quantize(Decimal("0.01"))
