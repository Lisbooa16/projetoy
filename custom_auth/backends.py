from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        user = None
        if username:
            try:
                user = UserModel.objects.get(email__iexact=username)
            except UserModel.DoesNotExist:
                try:
                    user = UserModel.objects.get(username__iexact=username)
                except UserModel.DoesNotExist:
                    return None
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
