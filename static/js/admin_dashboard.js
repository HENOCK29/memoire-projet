const presencesTable = document.getElementById('presences-body');
const absentsTable = document.getElementById('absents-repetition');
const assidusTable = document.getElementById('assidus');
const cloturerButtons = document.querySelectorAll('.cloturer-seance');

function updatePresences() {
    console.log("Début de la mise à jour des présences et statistiques...");
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) {
        console.error('Token CSRF manquant');
        presencesTable.innerHTML = '<tr><td colspan="5">Erreur : Token CSRF manquant</td></tr>';
        return;
    }

    fetch('/admin/presences/', {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'X-CSRFToken': csrfToken,
            'Authorization': `Bearer ${document.getElementById('access_token')?.value || ''}`
        },
        credentials: 'include'
    })
        .then(response => {
            console.log(`Réponse de /admin/presences/: ${response.status} ${response.statusText}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Erreur HTTP: ${response.status} ${response.statusText} - ${text}`);
                });
            }
            return response.json();
        })
        .then(presences => {
            console.log("Présences récupérées:", JSON.stringify(presences, null, 2));
            presencesTable.innerHTML = '';
            if (!Array.isArray(presences) || presences.length === 0) {
                console.log("Aucune présence à afficher");
                presencesTable.innerHTML = '<tr><td colspan="5">Aucune présence enregistrée</td></tr>';
            } else {
                presences.forEach(p => {
                    console.log(`Ajout de la présence: ${p.etudiant.nom} ${p.etudiant.prenom} - ${p.cours.nom}`);
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${p.etudiant.nom} ${p.etudiant.prenom} (${p.etudiant.matricule})</td>
                        <td>${p.cours.nom}</td>
                        <td>${p.date}</td>
                        <td>${p.heure}</td>
                        <td>${p.seance ? `${p.seance.cours.nom} - ${p.seance.salle}` : 'Aucune séance'}</td>
                    `;
                    presencesTable.appendChild(row);
                });
            }
        })
        .catch(err => {
            console.error('Erreur lors du chargement des présences:', err.message);
            presencesTable.innerHTML = `<tr><td colspan="5">Erreur lors du chargement des présences : ${err.message}</td></tr>`;
        });

    fetch('/admin/stats/', {
        headers: {
            'Accept': 'application/json',
            'X-CSRFToken': csrfToken,
            'Authorization': `Bearer ${document.getElementById('access_token')?.value || ''}`
        },
        credentials: 'include'
    })
        .then(response => {
            console.log(`Réponse de /admin/stats/: ${response.status} ${response.statusText}`);
            if (!response.ok) throw new Error(`Erreur HTTP: ${response.status} ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            console.log("Statistiques récupérées:", JSON.stringify(data, null, 2));
            const ctxCours = document.getElementById('presencesParCoursChart').getContext('2d');
            new Chart(ctxCours, {
                type: 'bar',
                data: {
                    labels: data.presences_par_cours.map(p => p.cours__nom),
                    datasets: [{
                        label: 'Présences par cours',
                        data: data.presences_par_cours.map(p => p.total),
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });

            const ctxDate = document.getElementById('presencesParDateChart').getContext('2d');
            new Chart(ctxDate, {
                type: 'line',
                data: {
                    labels: data.presences_par_date.map(p => p.date),
                    datasets: [{
                        label: 'Présences par date',
                        data: data.presences_par_date.map(p => p.total),
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        borderColor: 'rgba(153, 102, 255, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });

            absentsTable.innerHTML = '';
            if (data.absents_repetition.length === 0) {
                absentsTable.innerHTML = '<tr><td colspan="4">Aucun étudiant absent à répétition</td></tr>';
            } else {
                data.absents_repetition.forEach(a => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${a.nom}</td>
                        <td>${a.prenom}</td>
                        <td>${a.matricule}</td>
                        <td>${a.presences}</td>
                    `;
                    absentsTable.appendChild(row);
                });
            }

            assidusTable.innerHTML = '';
            if (data.assidus.length === 0) {
                assidusTable.innerHTML = '<tr><td colspan="4">Aucun étudiant assidu</td></tr>';
            } else {
                data.assidus.forEach(a => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${a.nom}</td>
                        <td>${a.prenom}</td>
                        <td>${a.matricule}</td>
                        <td>${a.presences}</td>
                    `;
                    assidusTable.appendChild(row);
                });
            }
        })
        .catch(err => console.error('Erreur lors de la mise à jour des stats:', err));
}

cloturerButtons.forEach(button => {
    button.addEventListener('click', () => {
        const seanceId = button.getAttribute('data-seance-id');
        console.log(`Tentative de clôture de la séance ${seanceId}`);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) {
            console.error('Token CSRF manquant');
            alert('Erreur : Token CSRF manquant');
            return;
        }
        fetch(`/admin/cloturer_seance/${seanceId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'Authorization': `Bearer ${document.getElementById('access_token')?.value || ''}`
            },
            credentials: 'include'
        })
        .then(response => {
            console.log(`Réponse de /admin/cloturer_seance/${seanceId}/: ${response.status} ${response.statusText}`);
            if (!response.ok) throw new Error(`Erreur HTTP: ${response.status} ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            console.log('Réponse JSON:', data);
            if (data.error) {
                alert('Erreur : ' + data.error);
            } else {
                alert(data.message);
                location.reload();
            }
        })
        .catch(err => {
            console.error('Erreur lors de la clôture:', err);
            alert('Erreur : ' + err);
        });
    });
});

// Mettre à jour toutes les 5 secondes
setInterval(updatePresences, 5000);
updatePresences();