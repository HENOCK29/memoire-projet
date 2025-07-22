const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas');
const overlay = document.getElementById('overlay');
const context = canvas && canvas.getContext('2d');
const overlayContext = overlay && overlay.getContext('2d');
const coursSelect = document.getElementById('cours');
const result = document.getElementById('result');

function init() {
    console.log("webcam.js chargé");
    if (!video || !canvas || !overlay || !coursSelect || !result) {
        console.error("Éléments DOM manquants:", { video, canvas, overlay, coursSelect, result });
        result.textContent = "Erreur : Éléments de la page manquants";
        result.className = 'alert alert-danger';
        return false;
    }
    // Ajuster les dimensions du canvas pour correspondre à la vidéo
    const updateCanvasSize = () => {
        const videoWidth = video.offsetWidth || 640;
        const videoHeight = video.offsetHeight || 480;
        canvas.width = videoWidth;
        canvas.height = videoHeight;
        overlay.width = videoWidth;
        overlay.height = videoHeight;
        console.log(`Dimensions canvas ajustées: ${videoWidth}x${videoHeight}`);
    };
    updateCanvasSize();
    window.addEventListener('resize', updateCanvasSize);
    return true;
}

// Vérifier l'initialisation avant de continuer
if (!init()) {
    console.error("Initialisation échouée, arrêt du script");
} else {
    // Contraintes pour la caméra : essayer la caméra frontale, fallback sur n'importe quelle caméra
    const constraints = {
        video: {
            facingMode: { ideal: 'user' }, // Caméra frontale préférée
            width: { ideal: 640, max: 1280 },
            height: { ideal: 480, max: 720 }
        }
    };

    navigator.mediaDevices.getUserMedia(constraints)
        .then(stream => {
            console.log("Webcam activée avec contraintes:", JSON.stringify(constraints));
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                video.play().catch(err => {
                    console.error("Erreur lors de la lecture de la vidéo:", err.name, err.message);
                    result.textContent = `Erreur de lecture vidéo : ${err.name} - ${err.message}`;
                    result.className = 'alert alert-danger';
                });
                detectFaces();
            };
        })
        .catch(err => {
            console.error("Erreur d'accès à la webcam:", err.name, err.message);
            let errorMessage = `Erreur d’accès à la webcam : ${err.name} - ${err.message}`;
            if (err.name === 'NotAllowedError') {
                errorMessage = "Accès à la caméra refusé. Veuillez autoriser l'accès à la caméra dans les paramètres du navigateur.";
            } else if (err.name === 'NotFoundError') {
                errorMessage = "Aucune caméra détectée sur cet appareil.";
            } else if (err.name === 'SecurityError') {
                errorMessage = "Accès à la caméra bloqué. Utilisez HTTPS ou vérifiez les paramètres de sécurité.";
            }
            result.textContent = errorMessage;
            result.className = 'alert alert-danger';
        });
}

async function detectFaces() {
    try {
        console.log("Vérification de face-api.js...");
        if (!window.faceapi || !window.faceapi.nets || !window.faceapi.nets.tinyFaceDetector) {
            throw new Error("face-api.js ou tinyFaceDetector non disponible");
        }
        console.log("face-api.js chargé");
        console.log("Chargement des modèles depuis /static/models/...");
        await window.faceapi.nets.tinyFaceDetector.loadFromUri('/static/models/');
        console.log("Modèles chargés");

        const input = video;
        setInterval(async () => {
            try {
                const detections = await window.faceapi.detectAllFaces(input, new window.faceapi.TinyFaceDetectorOptions({
                    inputSize: 512, // Optimisé pour mobile
                    scoreThreshold: 0.5
                }));
                overlayContext.clearRect(0, 0, overlay.width, overlay.height);
                console.log("Détections:", detections.length, "visages");
                if (detections.length > 0) {
                    detections.forEach(detection => {
                        const box = detection.box;
                        overlayContext.strokeStyle = 'green';
                        overlayContext.lineWidth = 2;
                        overlayContext.strokeRect(box.x, box.y, box.width, box.height);
                        overlayContext.fillStyle = 'green';
                        overlayContext.font = '20px Arial';
                        overlayContext.fillText('Visage détecté', box.x, box.y - 10);
                    });
                    result.textContent = 'Visage détecté';
                    result.className = 'alert alert-success';
                } else {
                    result.textContent = 'Aucun visage détecté';
                    result.className = 'alert alert-warning';
                }
            } catch (err) {
                console.error("Erreur lors de la détection de visages:", err);
            }
        }, 100);
    } catch (err) {
        console.error("Erreur lors du chargement de face-api.js ou des modèles:", err);
        result.textContent = `Erreur : Impossible de charger la détection faciale - ${err.message}`;
        result.className = 'alert alert-danger';
    }
}

function captureImage() {
    console.log("Bouton capturer cliqué");
    if (!context) {
        console.error("Contexte canvas manquant");
        result.textContent = "Erreur : Contexte canvas manquant";
        result.className = 'alert alert-danger';
        return;
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    const coursId = coursSelect.value;
    console.log("Envoi à l'API:", { cours_id: coursId, image_length: imageData.length });

    const token = window.accessToken;
    if (!token) {
        console.error("Token JWT manquant");
        result.textContent = "Erreur : Token JWT manquant";
        result.className = 'alert alert-danger';
        return;
    }

    fetch('/api/etudiant/presence/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
        },
        body: JSON.stringify({ image: imageData, cours_id: coursId })
    })
    .then(response => {
        console.log("Réponse API:", response.status, response.statusText);
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `Erreur HTTP: ${response.status} ${response.statusText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log("Données API:", data);
        if (data.error) {
            result.textContent = `Erreur : ${data.error}`;
            result.className = 'alert alert-danger';
        } else {
            result.textContent = 'Présence enregistrée avec succès !';
            result.className = 'alert alert-success';
        }
    })
    .catch(err => {
        console.error("Erreur fetch:", err);
        result.textContent = `Erreur : ${err.message}`;
        result.className = 'alert alert-danger';
    });
}