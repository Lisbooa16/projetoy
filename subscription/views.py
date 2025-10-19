from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from custom_auth.models import Vendedor


# Create your views here.
class Vendedores(GenericAPIView):
    permission_classes = [
        AllowAny,
    ]

    def get(self, request):
        loja_id = request.query_params.get("loja")

        if not loja_id:
            return Response({"detail": "Informe o parâmetro ?loja="}, status=400)

        vendedores = Vendedor.objects.filter(nome_loja_id=loja_id).values("id", "nome")
        data = list(vendedores)

        return Response(data)
