FROM python:3.10

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    pkg-config \
    libmysqlclient-dev \
    default-libmysqlclient-dev \
    build-essential \
    cmake \
    libpng-dev \
    libjpeg-dev \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    && apt-get clean

# Définir le dossier de travail
WORKDIR /app

# Copier les dépendances Python
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l’application
COPY . .

# Collecter les fichiers statiques (si applicable)
RUN python manage.py collectstatic --noinput

# Commande de démarrage
CMD ["sh", "-c", "python manage.py migrate && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT"]
