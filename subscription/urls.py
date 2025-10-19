from django.urls import path

from subscription.views import Vendedores

urlpatterns = [path("vendedores/", Vendedores.as_view())]
