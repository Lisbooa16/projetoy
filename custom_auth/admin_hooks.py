from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.db.utils import  OperationalError, ProgrammingError

from custom_auth.models import ActionPermission
from custom_auth.permissions import has_group_action

_original_has_view_permission = admin.ModelAdmin.has_view_permission
_original_has_change_permission = admin.ModelAdmin.has_change_permission
_original_has_delete_permission = admin.ModelAdmin.has_delete_permission
_original_has_add_permission = admin.ModelAdmin.has_add_permission
_original_get_model_perms = admin.ModelAdmin.get_model_perms
_original_get_actions = admin.ModelAdmin.get_actions


def _petched_get_actions(self, request):
    model_name = f"{self.model._meta.app_label}.{self.model._meta.model_name}"
    print(model_name)

    allowed_actions = request.user.allowed_actions.filter(model_name=model_name)

    if not allowed_actions:
        return _original_get_actions(self, request)

    filtred = {}

    for action in allowed_actions:

        def dynamic_actions(self, request, queryset, _name=action.name):
            if hasattr(self, _name):
                func = getattr(self, _name)
                return  func(request, queryset)
            self.message_user(
                request,
                f"Ação {_name} executada para {queryset.count()} registro(s)."
            )

        filtred[action.name] = (
            dynamic_actions,
            action,
            getattr(action, 'label', action.name.replace('_', ' ').title())
        )
    return filtred

def _patched_has_view_permission(self, request, obj=None):
    model_name = f"{self.model._meta.app_label}.{self.model._meta.model_name}"
    return has_group_action(request.user, model_name, 'view') or has_group_action(
        request.user, model_name, 'readonly'
    )


def _patched_has_change_permission(self, request, obj=None):
    model_name = f"{self.model._meta.app_label}.{self.model._meta.model_name}"
    return has_group_action(request.user, model_name, 'edit')


def _patched_has_delete_permission(self, request, obj=None):
    model_name = f"{self.model._meta.app_label}.{self.model._meta.model_name}"
    return has_group_action(request.user, model_name, 'delete')


def _patched_has_add_permission(self, request):
    model_name = f"{self.model._meta.app_label}.{self.model._meta.model_name}"
    # 'edit' também libera 'add'
    return has_group_action(request.user, model_name, 'edit')


def sync_action_permissions():
    """
    Sincroniza automaticamente todas as actions declaradas nos ModelAdmins registrados.
    Executa apenas uma vez, durante o carregamento do Django Admin.
    """
    try:
        created = 0

        for model, model_admin in admin.site._registry.items():
            model_name = model._meta.model_name
            actions = getattr(model_admin, 'actions', [])

            if isinstance(actions, dict):
                action_names = [k for k in actions.keys() if k.strip()]
            elif isinstance(actions, (list, tuple)):  # noqa: UP038
                action_names = [getattr(a, '__name__', str(a)) for a in actions if a]
            else:
                continue

            for name in action_names:
                _, was_created = ActionPermission.objects.get_or_create(
                    name=name,
                    model_name=model_name,
                )
                if was_created:
                    created += 1

        if created:
            print(f'[ActionPermission] {created} novas actions sincronizadas.')
    except (OperationalError, ProgrammingError):
        # ignora se o banco ainda não está migrado
        pass


def _patched_has_perm(self, perm, obj=None):
    """
    Ignora o sistema padrão de permissões do Django
    e delega tudo para o nosso has_group_action().
    """
    try:
        app_label, action_model = perm.split('.', 1)
        action, model_name = action_model.split('_', 1)
    except ValueError:
        # perm não segue o padrão app_label.action_model
        return False

    from custom_auth.permissions import has_group_action
    return has_group_action(self, model_name, action)


def _patched_has_module_perms(self, app_label):
    """
    Retorna True para todos os apps, para garantir que o admin
    carregue os ModelAdmins e nossos patches possam rodar.
    """
    return True


# Hook executado automaticamente quando o admin é carregado
sync_action_permissions()

AbstractUser.has_perm = _patched_has_perm
AbstractUser.has_module_perms = _patched_has_module_perms
admin.ModelAdmin.has_view_permission = _patched_has_view_permission
admin.ModelAdmin.has_change_permission = _patched_has_change_permission
admin.ModelAdmin.has_delete_permission = _patched_has_delete_permission
admin.ModelAdmin.has_add_permission = _patched_has_add_permission
admin.ModelAdmin.get_actions = _petched_get_actions
