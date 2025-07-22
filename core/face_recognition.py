import face_recognition
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import json

def get_face_encoding(image_path):
    try:
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        print(f"Encodages faciaux générés: {len(encodings)} visages détectés pour {image_path}")
        if not encodings:
            print(f"Aucun visage détecté dans {image_path}")
            return None
        return encodings[0].tolist()
    except Exception as e:
        print(f"Erreur lors de l'encodage facial pour {image_path}: {e}")
        return None

def compare_faces(known_encoding, unknown_encoding):
    try:
        # Vérifier si known_encoding est une chaîne JSON
        if isinstance(known_encoding, str):
            known_encoding = json.loads(known_encoding)
        # Sinon, supposer que c'est une liste ou un tableau numpy
        known = np.array(known_encoding, dtype=np.float64)
        unknown = np.array(unknown_encoding, dtype=np.float64)

        # Comparer les encodages
        distance = face_recognition.face_distance([known], unknown)[0]
        threshold = 0.4  # Seuil plus strict
        print(f"Distance faciale: {distance}, Seuil: {threshold}")
        return distance <= threshold, distance
    except Exception as e:
        print(f"Erreur lors de la comparaison faciale: {str(e)}")
        return False, f"Erreur: {str(e)}"