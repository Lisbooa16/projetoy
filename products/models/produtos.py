from django.db import models

from products.models.models_utils import BaseModel


class Categoria(BaseModel):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["nome"]),
        ]
        get_latest_by = "created_at"


class Produto(BaseModel):
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    codigo_barras = models.CharField(max_length=100, unique=True, blank=True, null=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, related_name="produtos"
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["nome"]),
        ]
        get_latest_by = "created_at"


class Promocao(BaseModel):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    produtos = models.ManyToManyField(Produto, related_name="promocoes", blank=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Promoção"
        verbose_name_plural = "Promoções"
        ordering = ["-data_inicio"]
        indexes = [
            models.Index(fields=["nome"]),
            models.Index(fields=["data_inicio"]),
            models.Index(fields=["data_fim"]),
        ]
        get_latest_by = "created_at"
