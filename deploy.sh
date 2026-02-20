#!/bin/bash
# Deploy Guenther to a remote server
# Usage: ./deploy.sh <server-ip> [user]
# Example: ./deploy.sh 77.42.36.29 root

set -e

SERVER=${1:?"Usage: ./deploy.sh <server-ip> [user]"}
USER=${2:-root}
REMOTE_DIR="/opt/guenther"

echo "=== Deploying Guenther to ${USER}@${SERVER} ==="

# Sync project files to server
echo ">> Syncing files..."
rsync -avz --exclude 'node_modules' \
           --exclude 'frontend/dist' \
           --exclude '__pycache__' \
           --exclude 'data' \
           --exclude '.git' \
           --exclude '.env' \
           -e ssh \
           . "${USER}@${SERVER}:${REMOTE_DIR}/"

# Build and start on server
echo ">> Building and starting container..."
ssh "${USER}@${SERVER}" << 'REMOTE_SCRIPT'
cd /opt/guenther

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Build and start
docker compose down || true
docker compose up -d --build

echo ""
echo "=== Guenther is running ==="
echo "Access: http://$(hostname -I | awk '{print $1}')"
docker compose ps
REMOTE_SCRIPT

echo ""
echo "=== Deploy complete ==="
echo "Access: http://${SERVER}"
