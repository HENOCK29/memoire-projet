# Generated by Django 5.2 on 2025-07-14 11:50

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Cours",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=200)),
                ("code", models.CharField(max_length=20, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Etudiant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=100)),
                ("prenom", models.CharField(max_length=100)),
                ("matricule", models.CharField(max_length=50, unique=True)),
                ("photo", models.ImageField(upload_to="etudiants/photos/")),
                ("face_encoding", models.TextField(blank=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Paiement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("montant", models.DecimalField(decimal_places=2, max_digits=10)),
                ("date", models.DateField(default=django.utils.timezone.now)),
                (
                    "type_frais",
                    models.CharField(
                        choices=[
                            ("SCOLARITE", "Frais de scolarité"),
                            ("INSCRIPTION", "Frais d’inscription"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "etudiant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.etudiant"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UtilisateurRole",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("ADMIN", "Administrateur"),
                            ("ETUDIANT", "Étudiant"),
                            ("CONTROLEUR", "Contrôleur"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Presence",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(default=django.utils.timezone.now)),
                ("heure", models.TimeField(default=django.utils.timezone.now)),
                (
                    "cours",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.cours"
                    ),
                ),
                (
                    "etudiant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.etudiant"
                    ),
                ),
            ],
            options={
                "unique_together": {("etudiant", "cours", "date")},
            },
        ),
    ]
