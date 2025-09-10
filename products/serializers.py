from rest_framework.serializers import ModelSerializer

from .models import Categoria as CategoryModel
from .models import Produto as ProductModel
from .models import Promocao as PromotionModel


class CategorySerializer(ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = ["id", "nome", "descricao"]
        read_only_fields = ["id"]  # ID é somente leitura


class ProductSerializer(ModelSerializer):
    class Meta:
        model = ProductModel
        fields = [
            "id",
            "nome",
            "descricao",
            "preco",
            "estoque",
            "codigo_barras",
            "categoria",
        ]
        read_only_fields = ["id"]  # ID é somente leitura


class PromotionSerializer(ModelSerializer):
    class Meta:
        model = PromotionModel
        fields = [
            "id",
            "nome",
            "descricao",
            "desconto_percentual",
            "data_inicio",
            "data_fim",
            "produtos",
        ]
        read_only_fields = ["id"]  # ID é somente leitura
