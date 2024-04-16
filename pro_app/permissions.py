from rest_framework import permissions

class ReadOnlyOrAdminPermission(permissions.BasePermission):
    """
    Custom permission to allow read access to all users
    but restrict write access to admin users only.
    """

    def has_permission(self, request, view):
        # Allow read access to all users (GET requests)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Restrict write access to admin users only (POST, PUT, DELETE requests)
        return request.user and request.user.is_staff