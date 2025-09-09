from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import viewsets, mixins, permissions, decorators, response, status
from .serializers import UserSerializer, UserCreateSerializer, GroupSerializer
from .permissions import IsSelfOrAdmin, IsReadOnlyOrAdmin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail

from rest_framework import viewsets, permissions, decorators, response, status
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle

from .serializers import (
    UserSerializer, UserCreateSerializer, GroupSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["list", "destroy", "partial_update", "update"]:
            # somente staff/admin podem listar e alterar outros
            return [permissions.IsAdminUser()]
        if self.action in ["create"]:
            # permitir registro público (sem auth)
            return [permissions.AllowAny()]
        if self.action in ["retrieve"]:
            # admin pode ver qualquer; user só a si mesmo via /me
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    @decorators.action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Retorna os dados do usuário autenticado"""
        ser = UserSerializer(request.user)
        return response.Response(ser.data)
    
    @decorators.action(
        detail=False, methods=["post"], url_path="me/change_password",
        permission_classes=[permissions.IsAuthenticated]
    )
    def change_password(self, request):
        ser = ChangePasswordSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        request.user.set_password(ser.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return response.Response({"detail": "Senha alterada com sucesso."}, status=status.HTTP_200_OK)

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAdminUser]


class PasswordResetRequestView(APIView):
    throttle_scope = "password_reset"
    throttle_classes = [ScopedRateThrottle]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = PasswordResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data["email"].lower().strip()
        redirect_url = ser.validated_data.get("redirect_url") or getattr(settings, "SITE_URL", "")

        try:
            user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            # Resposta genérica para não vazar existência de conta
            return response.Response({"detail": "Se o e-mail existir, você receberá as instruções."})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # Monte o link (front-end trataria uid/token)
        link = f"{redirect_url.rstrip('/')}/reset-password?uid={uid}&token={token}"

        subject = "Redefinição de senha"
        message = f"Olá,\n\nPara redefinir sua senha, acesse: {link}\n\nSe você não solicitou, ignore este e-mail."
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)

        return response.Response({"detail": "Se o e-mail existir, você receberá as instruções."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = PasswordResetConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        uid = ser.validated_data["uid"]
        token = ser.validated_data["token"]
        new_password = ser.validated_data["new_password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id, is_active=True)
        except Exception:
            return response.Response({"detail": "Link inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if not token_generator.check_token(user, token):
            return response.Response({"detail": "Token inválido ou expirado."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        return response.Response({"detail": "Senha redefinida com sucesso."}, status=status.HTTP_200_OK)