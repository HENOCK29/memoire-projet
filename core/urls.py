from django.urls import path
from django.views.generic import RedirectView
from .views import (
    home, admin_dashboard, admin_stats, admin_lancer_seance, admin_cloturer_seance,
    admin_presences, admin_export_csv, student_login, student_register, student_presence,
    EtudiantLoginView, EtudiantPresenceView, ControleurLoginView, ControleurVerifierView
)

urlpatterns = [
    path('', home, name='home'),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/stats/', admin_stats, name='admin_stats'),
    path('admin/presences/', admin_presences, name='admin_presences'),
    path('admin/lancer_seance/', admin_lancer_seance, name='admin_lancer_seance'),
    path('admin/cloturer_seance/<int:seance_id>/', admin_cloturer_seance, name='admin_cloturer_seance'),
    path('admin/export_csv/', admin_export_csv, name='admin_export_csv'),
    path('student/', RedirectView.as_view(url='/student/login/'), name='student_home'),
    path('student/register/', student_register, name='student_register'),
    path('student/login/', student_login, name='student_login'),
    path('student/presence/', student_presence, name='student_presence'),
    path('api/etudiant/login/', EtudiantLoginView.as_view(), name='etudiant_login'),
    path('api/etudiant/presence/', EtudiantPresenceView.as_view(), name='etudiant_presence'),
    path('api/controleur/login/', ControleurLoginView.as_view(), name='controleur_login'),
    path('api/controleur/verifier/', ControleurVerifierView.as_view(), name='controleur_verifier'),
]