from rest_framework import serializers
from .models import Etudiant, Cours, Presence, Seance, Paiement

class EtudiantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Etudiant
        fields = ['nom', 'prenom', 'matricule']

class CoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cours
        fields = ['nom']

class SeanceSerializer(serializers.ModelSerializer):
    cours = CoursSerializer()

    class Meta:
        model = Seance
        fields = ['cours', 'salle']

class PresenceSerializer(serializers.ModelSerializer):
    etudiant = EtudiantSerializer()
    cours = CoursSerializer()
    seance = SeanceSerializer(allow_null=True)

    class Meta:
        model = Presence
        fields = ['id', 'etudiant', 'cours', 'date', 'heure', 'seance']

    def to_representation(self, instance):
        # S'assurer que les champs date et heure sont correctement formatés
        representation = super().to_representation(instance)
        representation['date'] = instance.date.strftime('%Y-%m-%d')
        representation['heure'] = instance.heure.strftime('%H:%M:%S')
        return representation

class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = ['id', 'etudiant', 'montant', 'date', 'type_frais']