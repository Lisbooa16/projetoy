from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import User


DEFAULT_GROUPS = {
    "Administrators": {
        "permissions": ["add_user", "change_user", "delete_user", "view_user"],
    },
    "Managers": {
        "permissions": ["change_user", "view_user"],
    },
    "Operators": {
        "permissions": ["view_user"],
    },
}


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """
    Cria grupos padrões e associa permissões do model User.
    Roda após 'migrate'.
    """
    if sender.name != "custom_auth":
        return

    user_ct = ContentType.objects.get_for_model(User)
    perms_by_codename = {p.codename: p for p in Permission.objects.filter(content_type=user_ct)}
    for group_name, cfg in DEFAULT_GROUPS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        group.permissions.set([perms_by_codename[c] for c in cfg["permissions"] if c in perms_by_codename])
        group.save()
