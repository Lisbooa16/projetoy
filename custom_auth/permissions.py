from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_superuser:
            return True
        return obj == request.user

class IsReadOnlyOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS) or (request.user and request.user.is_staff)
