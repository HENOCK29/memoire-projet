import face_recognition
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Etudiant, Cours, Presence, Seance, UtilisateurRole, Paiement
from .serializers import PresenceSerializer, PaiementSerializer
from .face_recognition import compare_faces
from .permissions import IsControleur
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count
import json
import csv
from io import StringIO
import base64
from io import BytesIO
from PIL import Image
import numpy as np


def home(request):
    return render(request, 'home.html')


import re
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from core.models import Etudiant, UtilisateurRole
import logging

logger = logging.getLogger('django')

def student_register(request):
    if request.method == 'POST':
        matricule = request.POST.get('matricule')
        password = request.POST.get('password')
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        photo = request.FILES.get('photo')
        # Validation matricule (SI suivi de 4 chiffres)
        if not re.match(r'^SI\d{4}$', matricule):
            messages.error(request, "Matricule invalide. Format attendu : SIxxxx (ex: SI2005)")
            logger.error(f"Tentative d'inscription avec matricule invalide: {matricule}")
            return render(request, 'student/register.html')
        # Validation photo
        if photo:
            if photo.size > 5 * 1024 * 1024:  # 5MB max
                messages.error(request, "La photo ne doit pas dépasser 5 Mo.")
                logger.error(f"Photo trop grande pour {matricule}: {photo.size} bytes")
                return render(request, 'student/register.html')
            if not photo.content_type.startswith('image/'):
                messages.error(request, "Le fichier doit être une image (JPEG, PNG).")
                logger.error(f"Type de fichier invalide pour {matricule}: {photo.content_type}")
                return render(request, 'student/register.html')
        # Validation champs vides
        if not all([matricule, password, nom, prenom, photo]):
            messages.error(request, "Tous les champs sont obligatoires.")
            logger.error(f"Champs manquants pour inscription: {matricule}")
            return render(request, 'student/register.html')
        try:
            if User.objects.filter(username=matricule).exists():
                messages.error(request, "Matricule déjà utilisé")
                logger.error(f"Matricule déjà utilisé: {matricule}")
                return render(request, 'student/register.html')
            user = User.objects.create_user(username=matricule, password=password)
            etudiant = Etudiant.objects.create(
                nom=nom,
                prenom=prenom,
                matricule=matricule,
                user=user,
                photo=photo
            )
            UtilisateurRole.objects.create(user=user, role='ETUDIANT')
            messages.success(request, "Inscription réussie ! En attente de validation par l'administrateur.")
            logger.info(f"Inscription réussie pour {matricule}")
            return redirect('student_login')
        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")
            logger.error(f"Erreur inscription {matricule}: {str(e)}")
            return render(request, 'student/register.html')
    return render(request, 'student/register.html')


def student_login(request):
    if request.method == 'POST':
        matricule = request.POST.get('matricule')
        password = request.POST.get('password')
        try:
            etudiant = Etudiant.objects.get(matricule=matricule)
            user = authenticate(request, username=etudiant.user.username, password=password)
            if user and UtilisateurRole.objects.filter(user=user, role='ETUDIANT').exists():
                login(request, user)
                refresh = RefreshToken.for_user(user)
                token = str(refresh.access_token)
                print(f"Redirection vers /student/presence/ avec token: {token[:10]}...")
                return render(request, 'student/presence.html', {  # Changé de core/presence.html à student/presence.html
                    'cours_list': Cours.objects.all(),
                    'access_token': token,
                    'user': user
                })
            print("Échec de l'authentification")
            messages.error(request, "Identifiants invalides")
            return render(request, 'student/login.html')
        except Etudiant.DoesNotExist:
            print(f"Étudiant non trouvé pour matricule: {matricule}")
            messages.error(request, "Matricule invalide")
            return render(request, 'student/login.html')
    print("Affichage de la page de connexion")
    return render(request, 'student/login.html')


@login_required
def student_presence(request):
    if not UtilisateurRole.objects.filter(user=request.user, role='ETUDIANT').exists():
        messages.error(request, "Accès réservé aux étudiants.")
        print(f"Accès non autorisé pour l'utilisateur {request.user.username} à /student/presence/")
        return redirect('home')
    refresh = RefreshToken.for_user(request.user)
    token = str(refresh.access_token)
    print(f"Accès à /student/presence/ pour l'utilisateur {request.user.username}")
    return render(request, 'student/presence.html', {  # Changé de core/presence.html à student/presence.html
        'cours_list': Cours.objects.all(),
        'access_token': token,
        'user': request.user
    })


@login_required
def admin_dashboard(request):
    if not UtilisateurRole.objects.filter(user=request.user, role='ADMIN').exists():
        messages.error(request, "Accès non autorisé")
        print(f"Accès non autorisé pour l'utilisateur {request.user.username} à /admin/dashboard/")
        return redirect('home')
    print(f"Accès à /admin/dashboard/ pour l'utilisateur {request.user.username}")
    return render(request, 'admin/dashboard.html', {
        'etudiants': Etudiant.objects.all(),
        'cours': Cours.objects.all(),
        'presences': Presence.objects.all(),
        'seances': Seance.objects.all()
    })


@login_required
def admin_lancer_seance(request):
    if not UtilisateurRole.objects.filter(user=request.user, role='ADMIN').exists():
        messages.error(request, "Accès non autorisé")
        print(f"Accès non autorisé pour l'utilisateur {request.user.username} à /admin/lancer_seance/")
        return redirect('home')
    if request.method == 'POST':
        cours_id = request.POST.get('cours')
        salle = request.POST.get('salle')
        try:
            cours = Cours.objects.get(id=cours_id)
            seance = Seance.objects.create(
                cours=cours,
                salle=salle,
                date=timezone.now().date(),
                heure_debut=timezone.now().time()
            )
            print(f"Séance lancée: {seance}")
            messages.success(request, f"Séance pour {cours.nom} lancée avec succès !")
            return redirect('admin_dashboard')
        except Exception as e:
            print(f"Erreur lors du lancement de la séance: {str(e)}")
            messages.error(request, f"Erreur : {str(e)}")
    return render(request, 'admin/lancer_seance.html', {  # Corrigé pour utiliser lancer_seance.html
        'cours': Cours.objects.all()
    })


@login_required
def admin_cloturer_seance(request, seance_id):
    if not UtilisateurRole.objects.filter(user=request.user, role='ADMIN').exists():
        print(f"Accès non autorisé pour l'utilisateur {request.user.username} à /admin/cloturer_seance/{seance_id}/")
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    print(f"Tentative de clôture de la séance {seance_id} par {request.user.username}")
    try:
        seance = Seance.objects.get(id=seance_id, est_terminee=False)
        seance.est_terminee = True
        seance.save()
        print(f"Séance clôturée: {seance}")
        return JsonResponse({'message': f"Séance pour {seance.cours.nom} clôturée avec succès !"})
    except Seance.DoesNotExist:
        print(f"Séance non trouvée ou déjà clôturée: {seance_id}")
        return JsonResponse({'error': 'Séance non trouvée ou déjà clôturée'}, status=404)
    except Exception as e:
        print(f"Erreur lors de la clôture de la séance {seance_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def admin_presences(request):
    if not UtilisateurRole.objects.filter(user=request.user, role='ADMIN').exists():
        print(f"Accès non autorisé pour l'utilisateur {request.user.username} à /admin/presences/")
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    try:
        presences = Presence.objects.all().select_related('etudiant', 'cours', 'seance')
        cours_id = request.GET.get('cours_id')
        date = request.GET.get('date')
        if cours_id:
            presences = presences.filter(cours_id=cours_id)
        if date:
            presences = presences.filter(date=date)
        serialized_data = PresenceSerializer(presences, many=True).data
        print(f"Présences récupérées pour /admin/presences/ (cours_id={cours_id}, date={date}): {presences.count()}")
        print(f"Données sérialisées: {json.dumps(serialized_data, indent=2)}")
        return JsonResponse(serialized_data, safe=False)
    except Exception as e:
        print(f"Erreur dans admin_presences: {str(e)}")
        return JsonResponse({'error': f'Erreur serveur: {str(e)}'}, status=500)


@login_required
def admin_stats(request):
    if not UtilisateurRole.objects.filter(user=request.user, role='ADMIN').exists():
        print(f"Accès non autorisé pour l'utilisateur {request.user.username} à /admin/stats/")
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    try:
        presences_par_cours = Presence.objects.values('cours__nom').annotate(total=Count('id'))
        presences_par_date = Presence.objects.values('date').annotate(total=Count('id'))
        total_etudiants = Etudiant.objects.count()
        total_cours = Cours.objects.count()
        total_presences = Presence.objects.count()
        taux_presence = total_presences / (total_etudiants * total_cours or 1)
        seuil_presence = total_cours * 0.5
        etudiants_absents = Etudiant.objects.annotate(presences_count=Count('presence')).filter(
            presences_count__lt=seuil_presence)
        absents_repetition = [
            {'nom': e.nom, 'prenom': e.prenom, 'matricule': e.matricule, 'presences': e.presences_count}
            for e in etudiants_absents
        ]
        seuil_assiduite = total_cours * 0.8
        etudiants_assidus = Etudiant.objects.annotate(presences_count=Count('presence')).filter(
            presences_count__gte=seuil_assiduite)
        assidus = [
            {'nom': e.nom, 'prenom': e.prenom, 'matricule': e.matricule, 'presences': e.presences_count}
            for e in etudiants_assidus
        ]
        print(f"Stats récupérées: {total_presences} présences, {total_etudiants} étudiants")
        return JsonResponse({
            'presences_par_cours': list(presences_par_cours),
            'presences_par_date': [
                {'date': item['date'].strftime('%Y-%m-%d'), 'total': item['total']}
                for item in presences_par_date
            ],
            'total_etudiants': total_etudiants,
            'total_presences': total_presences,
            'taux_presence': taux_presence,
            'absences': total_etudiants * total_cours - total_presences,
            'absents_repetition': absents_repetition,
            'assidus': assidus
        })
    except Exception as e:
        print(f"Erreur dans admin_stats: {str(e)}")
        return JsonResponse({'error': f'Erreur serveur: {str(e)}'}, status=500)


@login_required
def admin_export_csv(request):
    if not UtilisateurRole.objects.filter(user=request.user, role='ADMIN').exists():
        print(f"Accès non autorisé pour l'utilisateur {request.user.username} à /admin/export_csv/")
        return HttpResponse('Accès non autorisé', status=403)
    try:
        cours_id = request.GET.get('cours_id')
        date = request.GET.get('date')
        etudiant_id = request.GET.get('etudiant_id')
        presences = Presence.objects.all()
        if cours_id:
            presences = presences.filter(cours_id=cours_id)
        if date:
            presences = presences.filter(date=date)
        if etudiant_id:
            presences = presences.filter(etudiant_id=etudiant_id)
        print(f"Exportation CSV: {presences.count()} présences")
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Étudiant', 'Cours', 'Date', 'Heure', 'Séance'])
        for presence in presences:
            writer.writerow([
                presence.id,
                f"{presence.etudiant.nom} {presence.etudiant.prenom} ({presence.etudiant.matricule})",
                presence.cours.nom,
                presence.date.strftime('%Y-%m-%d'),
                presence.heure.strftime('%H:%M:%S'),
                f"{presence.seance.cours.nom} - {presence.seance.salle}" if presence.seance else ''
            ])
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="presences.csv"'
        response.write(output.getvalue())
        return response
    except Exception as e:
        print(f"Erreur dans admin_export_csv: {str(e)}")
        return HttpResponse(f'Erreur serveur: {str(e)}', status=500)


class EtudiantLoginView(APIView):
    def post(self, request):
        matricule = request.data.get('matricule')
        password = request.data.get('password')
        try:
            etudiant = Etudiant.objects.get(matricule=matricule)
            user = authenticate(request, username=etudiant.user.username, password=password)
            if user and UtilisateurRole.objects.filter(user=user, role='ETUDIANT').exists():
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                })
            print("Échec de l'authentification")
            return Response({'error': 'Identifiants invalides'}, status=status.HTTP_401_UNAUTHORIZED)
        except Etudiant.DoesNotExist:
            print(f"Étudiant non trouvé: {matricule}")
            return Response({'error': 'Matricule invalide'}, status=status.HTTP_400_BAD_REQUEST)


class ControleurLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        print(f"Tentative de connexion contrôleur: username={username}, password={password[:3]}... (tronqué pour sécurité)")
        try:
            user = authenticate(request, username=username, password=password)
            if user:
                print(f"Utilisateur authentifié: {username}")
                if UtilisateurRole.objects.filter(user=user, role='CONTROLEUR').exists():
                    print(f"Rôle CONTROLEUR confirmé pour {username}")
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'refresh': str(refresh),
                        'access': str(refresh.access_token)
                    })
                else:
                    print(f"Rôle CONTROLEUR non trouvé pour {username}")
                    return Response({'error': 'Utilisateur n’a pas le rôle CONTROLEUR'}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                print(f"Échec de l’authentification: username={username}, mot de passe incorrect ou utilisateur inexistant")
                return Response({'error': 'Identifiants invalides'}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(f"Erreur lors de la connexion contrôleur: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EtudiantPresenceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("Appel à EtudiantPresenceView")
        if not request.user.is_authenticated:
            print("Utilisateur non authentifié")
            return Response({'error': 'Utilisateur non authentifié'}, status=status.HTTP_401_UNAUTHORIZED)
        cours_id = request.data.get('cours_id')
        image_data = request.data.get('image')
        print(f"Données reçues: cours_id={cours_id}, image_data_length={len(image_data) if image_data else None}")
        try:
            etudiant = Etudiant.objects.get(user=request.user)
            print(f"Étudiant trouvé: {etudiant}")
            if not etudiant.face_encoding:
                print("Encodage facial manquant pour l'étudiant")
                return Response({'error': 'Encodage facial manquant pour votre profil'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                cours = Cours.objects.get(id=cours_id)
                print(f"Cours trouvé: {cours}")
            except Cours.DoesNotExist:
                print(f"Cours non trouvé: cours_id={cours_id}")
                return Response({'error': 'Cours invalide'}, status=status.HTTP_400_BAD_REQUEST)
            today = timezone.now().date()
            seance = Seance.objects.filter(cours=cours, date=today, est_terminee=False).first()
            if not seance:
                seances = Seance.objects.filter(cours=cours, date=today)
                print(f"Aucune séance active pour le cours {cours.nom} le {today}. Séances trouvées: {seances.count()}")
                for s in seances:
                    print(f"Séance ID: {s.id}, Date: {s.date}, Terminée: {s.est_terminee}")
                return Response({'error': "Aucune séance active pour ce cours aujourd'hui"},
                                status=status.HTTP_400_BAD_REQUEST)
            format, imgstr = image_data.split(';base64,')
            image = Image.open(BytesIO(base64.b64decode(imgstr)))
            image_np = np.array(image)
            face_locations = face_recognition.face_locations(image_np)
            if not face_locations:
                print("Aucun visage détecté dans l'image")
                return Response({'error': 'Aucun visage détecté dans l’image'}, status=status.HTTP_400_BAD_REQUEST)
            encodings = face_recognition.face_encodings(image_np, face_locations)
            if not encodings:
                print("Aucun encodage facial généré")
                return Response({'error': 'Aucun encodage facial généré'}, status=status.HTTP_400_BAD_REQUEST)
            encoding = encodings[0]
            is_match, distance = compare_faces(etudiant.face_encoding, encoding.tolist())
            print(f"Comparaison faciale: match={is_match}, distance={distance}")
            if not is_match:
                print(f"Échec de la reconnaissance: {distance}")
                return Response({'error': f'Visage non reconnu (distance: {distance})'}, status=status.HTTP_400_BAD_REQUEST)
            now = timezone.now().time()
            if Presence.objects.filter(etudiant=etudiant, cours=cours, date=today).exists():
                print(f"Présence déjà enregistrée pour {etudiant} - {cours} - {today}")
                return Response({'error': "Présence déjà enregistrée aujourd'hui pour ce cours"}, status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic():
                presence = Presence.objects.create(
                    etudiant=etudiant,
                    cours=cours,
                    seance=seance,
                    date=today,
                    heure=now
                )
                print(f"Présence enregistrée: {presence}")
                presence_exists = Presence.objects.filter(id=presence.id).exists()
                print(f"Présence existe dans la base: {presence_exists}")
                if not presence_exists:
                    raise Exception("Échec de l'enregistrement de la présence dans la base")
                serialized = PresenceSerializer(presence).data
                return Response({
                    'etat': 'enregistre',
                    'etudiant': {
                        'matricule': etudiant.matricule,
                        'nom': etudiant.nom,
                        'prenom': etudiant.prenom
                    },
                    'cours': cours.nom,
                    'date': serialized['date'],
                    'heure': serialized['heure'],
                    'message': f"Présence enregistrée pour {etudiant.nom} {etudiant.prenom} dans {cours.nom}"
                }, status=status.HTTP_201_CREATED)
        except IntegrityError:
            print("Erreur d'intégrité: Présence déjà enregistrée")
            return Response({'error': "Présence déjà enregistrée aujourd'hui"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur API: {str(e)}")
            return Response({'error': f"Erreur serveur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ControleurVerifierView(APIView):
    permission_classes = [IsAuthenticated, IsControleur]

    def post(self, request):
        image_data = request.data.get('image')
        type_frais = request.data.get('type_frais')
        print(f"Appel à ControleurVerifierView: type_frais={type_frais}, image_data_length={len(image_data) if image_data else None}")

        if not image_data or not type_frais:
            print("Données manquantes: image ou type_frais")
            return Response({'error': 'Image et type_frais requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            format, imgstr = image_data.split(';base64,')
            image = Image.open(BytesIO(base64.b64decode(imgstr)))
            image_np = np.array(image)
            face_locations = face_recognition.face_locations(image_np)
            if not face_locations:
                print("Aucun visage détecté dans l'image")
                return Response({
                    'etat': 'non_reconnu',
                    'message': 'Aucun visage détecté dans l’image.'
                }, status=status.HTTP_400_BAD_REQUEST)
            encodings = face_recognition.face_encodings(image_np, face_locations)
            if not encodings:
                print("Aucun encodage facial généré")
                return Response({
                    'etat': 'non_reconnu',
                    'message': 'Aucun encodage facial généré.'
                }, status=status.HTTP_400_BAD_REQUEST)
            encoding = encodings[0]

            for etudiant in Etudiant.objects.all():
                if not etudiant.face_encoding:
                    print(f"Encodage facial manquant pour {etudiant}")
                    continue
                try:
                    is_match, distance = compare_faces(etudiant.face_encoding, encoding.tolist())
                    print(f"Comparaison avec {etudiant.nom} {etudiant.prenom} ({etudiant.matricule}): match={is_match}, distance={distance}")
                    if is_match:
                        try:
                            paiement = Paiement.objects.filter(
                                etudiant=etudiant,
                                type_frais=type_frais.upper()
                            ).latest('date')
                            print(f"Paiement trouvé: {paiement}")
                            return Response({
                                'etat': 'reconnu',
                                'etudiant': {
                                    'matricule': etudiant.matricule,
                                    'nom': etudiant.nom,
                                    'prenom': etudiant.prenom
                                },
                                'paiement': {
                                    'type_frais': paiement.type_frais,
                                    'montant_du': float(paiement.montant_du),
                                    'montant_paye': float(paiement.montant_paye),
                                    'date': paiement.date.strftime('%Y-%m-%d'),
                                    'paye': paiement.paye
                                }
                            }, status=status.HTTP_200_OK)
                        except Paiement.DoesNotExist:
                            print(f"Aucun paiement trouvé pour {etudiant} - {type_frais}")
                            return Response({
                                'etat': 'reconnu',
                                'etudiant': {
                                    'matricule': etudiant.matricule,
                                    'nom': etudiant.nom,
                                    'prenom': etudiant.prenom
                                },
                                'paiement': {
                                    'type_frais': type_frais,
                                    'message': 'Aucun paiement trouvé pour ce type de frais.'
                                }
                            }, status=status.HTTP_200_OK)
                except Exception as e:
                    print(f"Erreur lors de la comparaison pour {etudiant.nom} {etudiant.prenom} ({etudiant.matricule}): {str(e)}")
                    continue
            print("Aucun étudiant identifié")
            return Response({
                'etat': 'non_reconnu',
                'message': 'L’étudiant n’a pas pu être identifié par reconnaissance faciale.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur dans ControleurVerifierView: {str(e)}")
            return Response({'error': f"Erreur serveur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)