# Generated by Django 5.2 on 2025-07-14 23:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_alter_etudiant_face_encoding_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cours",
            name="nom",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="presence",
            name="date",
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="presence",
            name="heure",
            field=models.TimeField(auto_now_add=True),
        ),
        migrations.CreateModel(
            name="Seance",
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
                ("date", models.DateField(auto_now_add=True)),
                ("heure_debut", models.TimeField(auto_now_add=True)),
                ("salle", models.CharField(max_length=50)),
                ("est_terminee", models.BooleanField(default=False)),
                (
                    "cours",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.cours"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="presence",
            name="seance",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to="core.seance"
            ),
        ),
    ]
