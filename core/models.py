import json
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .face_recognition import get_face_encoding
import os

class Etudiant(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    matricule = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='etudiants/photos/', null=True, blank=True)
    face_encoding = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Sauvegarder d'abord pour générer le chemin de la photo
        super().save(*args, **kwargs)
        if self.photo:
            try:
                photo_path = self.photo.path
                if os.path.exists(photo_path):
                    encoding = get_face_encoding(photo_path)
                    self.face_encoding = json.dumps(encoding) if encoding is not None else ''
                else:
                    print(f"Fichier non trouvé: {photo_path}")
                    self.face_encoding = ''
            except Exception as e:
                print(f"Erreur lors de la génération de l'encodage facial: {e}")
                self.face_encoding = ''
            super().save(update_fields=['face_encoding'])
        else:
            self.face_encoding = ''
            super().save(update_fields=['face_encoding'])

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.matricule})"

class Cours(models.Model):
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.nom

class Seance(models.Model):
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    heure_debut = models.TimeField(auto_now_add=True)
    salle = models.CharField(max_length=50)
    est_terminee = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.cours.nom} - {self.date} {self.heure_debut} - {self.salle}"

class Presence(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE)
    seance = models.ForeignKey(Seance, on_delete=models.CASCADE, null=True)
    date = models.DateField(auto_now_add=True)
    heure = models.TimeField(auto_now_add=True)

    class Meta:
        unique_together = ('etudiant', 'cours', 'date')

    def __str__(self):
        return f"{self.etudiant} - {self.cours} - {self.date}"

class Paiement(models.Model):
    TYPE_FRAIS = [
        ('SCOLARITE', 'Frais de scolarité'),
        ('INSCRIPTION', 'Frais d’inscription'),
    ]
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    type_frais = models.CharField(max_length=20, choices=TYPE_FRAIS)
    montant_du = models.DecimalField(max_digits=10, decimal_places=2)
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    paye = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.etudiant} - {self.type_frais} - {self.montant_paye}/{self.montant_du} - {self.date}"

class UtilisateurRole(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('ETUDIANT', 'Étudiant'),
        ('CONTROLEUR', 'Contrôleur'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"