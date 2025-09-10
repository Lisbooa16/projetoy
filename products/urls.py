from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import Category


urlpatterns = [
    path("categoria/", Category.as_view(), name="category-list"),
]