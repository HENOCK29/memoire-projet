from rest_framework import permissions
from .models import UtilisateurRole

class IsControleur(permissions.BasePermission):
    def has_permission(self, request, view):
        return UtilisateurRole.objects.filter(user=request.user, role='CONTROLEUR').exists()