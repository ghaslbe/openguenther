#!/bin/bash
set -e

CONTAINER_NAME="openguenther"
IMAGE_NAME="openguenther"
PORT="3333"
VOLUME="openguenther-data"

echo "==> OPENguenther Update"
echo ""

# Pull latest code from GitHub
echo "[1/4] Neuesten Code von GitHub holen..."
git pull

# Stop and remove old container
echo "[2/4] Alten Container stoppen..."
docker stop $CONTAINER_NAME 2>/dev/null && docker rm $CONTAINER_NAME 2>/dev/null || true

# Build new image
echo "[3/4] Neues Docker-Image bauen (das dauert ein paar Minuten)..."
docker build -t $IMAGE_NAME .

# Start new container
echo "[4/4] Container starten..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:5000 \
  -v $VOLUME:/app/data \
  --restart unless-stopped \
  $IMAGE_NAME

echo ""
echo "✓ Update abgeschlossen! OPENguenther läuft auf Port $PORT."
echo "  Deine Chats und Einstellungen sind erhalten geblieben."
