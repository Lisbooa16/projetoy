# apps/products/views.py
from rest_framework import status
from rest_framework.response import Response

from custom_auth.views_mixins import BaseFrontPerm
from products.serializers import CategorySerializer, ProductSerializer, PromotionSerializer
from .models import Categoria as CategoryModel
from .models import Produto as ProductModel
from .models import Promocao as PromotionModel


class Category(BaseFrontPerm):
    serializer_class = CategorySerializer
    required_perm_map = {
        "GET": "category.view",
        "POST": "category.create",
        "PUT": "category.update",
        "DELETE": "category.delete",
    }

    def get(self, request, *args, **kwargs):
        """Listar todas as categorias ou uma categoria específica por ID"""
        _id = request.query_params.get("id")
        if _id:
            try:
                category = CategoryModel.objects.get(id=_id)
            except CategoryModel.DoesNotExist:
                return Response({"error": "Categoria não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"id": category.id, "name": category.nome, "description": category.descricao}, status=status.HTTP_200_OK)

        categories = CategoryModel.objects.all().values("id", "nome", "descricao")
        return Response(categories, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Criar uma nova categoria"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        category = serializer.instance
        return Response({"id": category.id, "name": category.nome, "description": category.descricao}, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """Deletar uma categoria por ID"""
        category_id = request.query_params.get("id")
        if not category_id:
            return Response({"error": "ID da categoria é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            category = CategoryModel.objects.get(id=category_id)
        except CategoryModel.DoesNotExist:
            return Response({"error": "Categoria não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, *args, **kwargs):
        """Atualizar uma categoria existente por ID"""
        category_id = request.query_params.get("id")
        if not category_id:
            return Response({"error": "ID da categoria é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            category = CategoryModel.objects.get(id=category_id)
        except CategoryModel.DoesNotExist:
            return Response({"error": "Categoria não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(category, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        updated = serializer.instance
        return Response({"id": updated.id, "name": updated.nome, "description": updated.descricao}, status=status.HTTP_200_OK)


class Product(BaseFrontPerm):
    serializer_class = ProductSerializer
    required_perm_map = {
        "GET": "product.view",
        "POST": "product.create",
        "PUT": "product.update",
        "DELETE": "product.delete",
    }

    def get(self, request, *args, **kwargs):
        """Listar todos os produtos ou um produto específico por ID"""
        _id = request.query_params.get("id")
        if _id:
            try:
                product = ProductModel.objects.get(id=_id)
            except ProductModel.DoesNotExist:
                return Response({"error": "Produto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

            return Response({
                "id": product.id,
                "name": product.nome,
                "description": product.descricao,
                "price": product.preco,
                "stock": product.estoque,
                "barcode": product.codigo_barras,
                "category_id": product.categoria.id if product.categoria else None
            }, status=status.HTTP_200_OK)

        products = ProductModel.objects.all().values(
            "id", "nome", "descricao", "preco", "estoque", "codigo_barras", "categoria"
        )
        return Response(products, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Criar um novo produto"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        product = serializer.instance
        return Response({
            "id": product.id,
            "name": product.nome,
            "description": product.descricao,
            "price": product.preco,
            "stock": product.estoque,
            "barcode": product.codigo_barras,
            "category_id": product.categoria.id if product.categoria else None
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """Deletar um produto por ID"""
        product_id = request.query_params.get("id")
        if not product_id:
            return Response({"error": "ID do produto é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = ProductModel.objects.get(id=product_id)
        except ProductModel.DoesNotExist:
            return Response({"error": "Produto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, *args, **kwargs):
        """Atualizar um produto existente por ID"""
        product_id = request.query_params.get("id")
        if not product_id:
            return Response({"error": "ID do produto é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = ProductModel.objects.get(id=product_id)
        except ProductModel.DoesNotExist:
            return Response({"error": "Produto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(product, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        updated = serializer.instance
        return Response({
            "id": updated.id,
            "name": updated.nome,
            "description": updated.descricao,
            "price": updated.preco,
            "stock": updated.estoque,
            "barcode": updated.codigo_barras,
            "category_id": updated.categoria.id if updated.categoria else None
        }, status=status.HTTP_200_OK)


class Promotion(BaseFrontPerm):
    serializer_class = PromotionSerializer
    required_perm_map = {
        "GET": "promotion.view",
        "POST": "promotion.manage",
        "PUT": "promotion.manage",
        "DELETE": "promotion.manage",
    }

    def get(self, request, *args, **kwargs):
        """Listar todas as promoções ou uma promoção específica por ID"""
        _id = request.query_params.get("id")
        if _id:
            try:
                promotion = PromotionModel.objects.get(id=_id)
            except PromotionModel.DoesNotExist:
                return Response({"error": "Promoção não encontrada."}, status=status.HTTP_404_NOT_FOUND)

            return Response({
                "id": promotion.id,
                "name": promotion.nome,
                "description": promotion.descricao,
                "discount_percentage": promotion.desconto_percentual,
                "start_date": promotion.data_inicio,
                "end_date": promotion.data_fim,
                "product_ids": list(promotion.produtos.values_list("id", flat=True)),
            }, status=status.HTTP_200_OK)

        promotions = PromotionModel.objects.all().values(
            "id", "nome", "descricao", "desconto_percentual", "data_inicio", "data_fim"
        )
        return Response(promotions, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Criar uma nova promoção"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        promotion = serializer.instance
        return Response({
            "id": promotion.id,
            "name": promotion.nome,
            "description": promotion.descricao,
            "discount_percentage": promotion.desconto_percentual,
            "start_date": promotion.data_inicio,
            "end_date": promotion.data_fim,
            "product_ids": list(promotion.produtos.values_list("id", flat=True)),
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """Deletar uma promoção por ID"""
        promotion_id = request.query_params.get("id")
        if not promotion_id:
            return Response({"error": "ID da promoção é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            promotion = PromotionModel.objects.get(id=promotion_id)
        except PromotionModel.DoesNotExist:
            return Response({"error": "Promoção não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        promotion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, *args, **kwargs):
        """Atualizar uma promoção existente por ID"""
        promotion_id = request.query_params.get("id")
        if not promotion_id:
            return Response({"error": "ID da promoção é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            promotion = PromotionModel.objects.get(id=promotion_id)
        except PromotionModel.DoesNotExist:
            return Response({"error": "Promoção não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(promotion, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        updated = serializer.instance
        return Response({
            "id": updated.id,
            "name": updated.nome,
            "description": updated.descricao,
            "discount_percentage": updated.desconto_percentual,
            "start_date": updated.data_inicio,
            "end_date": updated.data_fim,
            "product_ids": list(updated.produtos.values_list("id", flat=True)),
        }, status=status.HTTP_200_OK)
