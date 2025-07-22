FROM python:3.11-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    libmariadb-dev-compat \
    libmariadb-dev \
    build-essential \
    cmake \
    libpng-dev \
    libjpeg-dev \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

# Définir le dossier de travail
WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le reste de l'application
COPY . .

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Démarrer l'application : migration + serveur
CMD ["sh", "-c", "python manage.py migrate && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT"]
