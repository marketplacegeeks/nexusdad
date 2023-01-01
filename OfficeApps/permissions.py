from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCheckerOrAdminForWrite(BasePermission):
    """
    Read-only for anyone on SAFE methods.
    Write access (create/update/deactivate) only for authenticated users in 'Checker' group or superusers.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        return user.is_superuser or user.groups.filter(name="Checker").exists()

    def has_object_permission(self, request, view, obj):
        # Same rules at the object level
        return self.has_permission(request, view)
