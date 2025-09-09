from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User
from .forms import UserCreationForm, UserChangeForm


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = ("username", "email", "display_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "display_name")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("display_name", "first_name", "last_name", "email", "public_id")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ("public_id",)
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "display_name", "password1", "password2", "is_staff", "is_active"),
        }),
    )
