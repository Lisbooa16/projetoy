# apps/products/admin.py
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.contrib import admin, messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import Categoria, Produto, Promocao

# -------------------- Inlines --------------------


class ProdutoInline(admin.TabularInline):
    model = Produto
    extra = 0
    fields = ("nome", "preco", "estoque", "codigo_barras")
    readonly_fields = ()
    show_change_link = True
    autocomplete_fields = ()
    ordering = ("nome",)


# -------------------- ListFilters custom --------------------


class EstoqueVazioFilter(admin.SimpleListFilter):
    title = "Estoque"
    parameter_name = "estoque_status"

    def lookups(self, request, model_admin):
        return (
            ("zerado", "Zerado (= 0)"),
            ("baixo", "Baixo (<= 5)"),
            ("positivo", "Positivo (> 0)"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "zerado":
            return queryset.filter(estoque=0)
        if value == "baixo":
            return queryset.filter(estoque__lte=5)
        if value == "positivo":
            return queryset.filter(estoque__gt=0)
        return queryset


class PromocaoAtivaFilter(admin.SimpleListFilter):
    title = "Ativa?"
    parameter_name = "ativa"

    def lookups(self, request, model_admin):
        return (("sim", "Sim"), ("nao", "Não"))

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == "sim":
            return queryset.filter(data_inicio__lte=now, data_fim__gte=now)
        if self.value() == "nao":
            return queryset.exclude(data_inicio__lte=now, data_fim__gte=now)
        return queryset


# -------------------- Admins --------------------


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "qtd_produtos", "created_at")
    search_fields = ("nome", "descricao")
    ordering = ("nome",)
    inlines = [ProdutoInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_prod_count=Count("produtos"))

    @admin.display(description="Qtd. produtos", ordering="_prod_count")
    def qtd_produtos(self, obj: Categoria):
        return getattr(obj, "_prod_count", 0)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "categoria",
        "preco",
        "estoque",
        "codigo_barras",
        "em_promocao",
    )
    list_filter = ("categoria", "promocoes", EstoqueVazioFilter)
    search_fields = ("nome", "descricao", "codigo_barras")
    ordering = ("nome",)
    autocomplete_fields = ("categoria",)
    date_hierarchy = "created_at"
    list_select_related = ("categoria",)
    actions = ["zerar_estoque", "aumentar_preco_10", "reduzir_preco_10"]

    @admin.display(description="Em promoção?", boolean=True)
    def em_promocao(self, obj: Produto):
        now = timezone.now()
        return obj.promocoes.filter(data_inicio__lte=now, data_fim__gte=now).exists()

    # --------- Ações em massa ---------

    def _ajustar_preco(self, request, queryset, percent, label):
        # remove qualquer select_related herdado do ChangeList
        qs = queryset.select_related(None).only("id", "preco")

        updated = 0
        for p in qs:
            novo = (Decimal(p.preco) * (Decimal("1.0") + percent)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if novo < 0:
                novo = Decimal("0.00")
            if novo != p.preco:
                Produto.objects.filter(pk=p.pk).update(preco=novo)
                updated += 1

        if updated:
            messages.success(request, f"{label}: {updated} produto(s) atualizado(s).")
        else:
            messages.info(request, "Nenhum produto precisou de atualização.")

    def aumentar_preco_10(self, request, queryset):
        self._ajustar_preco(
            request, queryset, Decimal("0.10"), "Aumento de 10% aplicado"
        )

    aumentar_preco_10.short_description = "Aumentar preço em 10%%"  # <- ESCAPADO

    def reduzir_preco_10(self, request, queryset):
        self._ajustar_preco(
            request, queryset, Decimal("-0.10"), "Redução de 10% aplicada"
        )

    reduzir_preco_10.short_description = "Reduzir preço em 10%%"  # <- ESCAPADO

    def zerar_estoque(self, request, queryset):
        updated = queryset.update(estoque=0)
        if updated:
            messages.warning(request, f"Estoque zerado em {updated} produto(s).")
        else:
            messages.info(request, "Nenhum produto atualizado.")

    zerar_estoque.short_description = "Zerar estoque"


@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "desconto_percentual",
        "data_inicio",
        "data_fim",
        "ativa_agora",
        "qtd_produtos",
    )
    list_filter = (PromocaoAtivaFilter, "data_inicio", "data_fim")
    search_fields = ("nome", "descricao", "produtos__nome", "produtos__codigo_barras")
    ordering = ("-data_inicio",)
    autocomplete_fields = ("produtos",)
    filter_horizontal = ()  # usando autocomplete para M2M
    date_hierarchy = "data_inicio"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_prod_count=Count("produtos"))

    @admin.display(description="Ativa agora?", boolean=True)
    def ativa_agora(self, obj: Promocao):
        now = timezone.now()
        return obj.data_inicio <= now <= obj.data_fim

    @admin.display(description="Qtd. produtos", ordering="_prod_count")
    def qtd_produtos(self, obj: Promocao):
        return getattr(obj, "_prod_count", 0)
