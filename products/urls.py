# apps/products/urls.py
from django.urls import path

from .views import Category, Product, Promotion

urlpatterns = [
    path("categoria/", Category.as_view(), name="category"),
    path("produto/", Product.as_view(), name="product"),
    path("promocao/", Promotion.as_view(), name="promotion"),
]
