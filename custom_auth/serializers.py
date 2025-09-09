from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.models import Group
from rest_framework import serializers


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        read_only_fields = ("id", "public_id", "is_superuser", "last_login", "date_joined")
        fields = (
            "id", "public_id", "username", "email", "display_name",
            "first_name", "last_name", "is_active", "is_staff",
            "groups", "last_login", "date_joined"
        )

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "email", "display_name", "password")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "name", "permissions")


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "Senha atual inválida."})
        # valida pelas regras do Django (AUTH_PASSWORD_VALIDATORS)
        password_validation.validate_password(attrs["new_password"], user=user)
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    # opcional: override do link de redirecionamento do front
    redirect_url = serializers.URLField(required=False)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        # valida força
        password_validation.validate_password(attrs["new_password"])
        return attrs