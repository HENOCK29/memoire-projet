from django.contrib import admin
from .models import Etudiant, Cours, Seance, Presence, Paiement, UtilisateurRole

@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'nom', 'prenom', 'user']
    search_fields = ['matricule', 'nom', 'prenom']

@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code']
    search_fields = ['nom', 'code']

@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = ['cours', 'date', 'heure_debut', 'salle', 'est_terminee']
    list_filter = ['cours', 'date', 'est_terminee']
    search_fields = ['cours__nom', 'salle']

@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ['etudiant', 'cours', 'date', 'heure', 'seance']
    list_filter = ['cours', 'date']
    search_fields = ['etudiant__matricule', 'etudiant__nom', 'cours__nom']

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['etudiant', 'type_frais', 'montant_du', 'montant_paye', 'date', 'paye']
    list_filter = ['type_frais', 'date', 'paye']
    search_fields = ['etudiant__matricule', 'etudiant__nom']

@admin.register(UtilisateurRole)
class UtilisateurRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter = ['role']
    search_fields = ['user__username']