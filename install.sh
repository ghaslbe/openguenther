#!/bin/bash
set -e

REPO_URL="https://github.com/ghaslbe/openguenther.git"
INSTALL_DIR="openguenther"
CONTAINER_NAME="openguenther"
IMAGE_NAME="openguenther"
PORT="3333"
VOLUME="openguenther-data"

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
info() { echo -e "${CYAN}→${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
fail() { echo -e "${RED}✗ $1${NC}"; exit 1; }

echo ""
echo -e "${BOLD}OPENguenther — Installer${NC}"
echo "──────────────────────────────────────"
echo ""

# ── OS detection ──────────────────────────────────────────────────────────────
OS="$(uname -s)"
case "$OS" in
  Linux*)  PLATFORM="Linux" ;;
  Darwin*) PLATFORM="macOS" ;;
  *)       fail "Nicht unterstütztes Betriebssystem: $OS" ;;
esac
ok "Betriebssystem: $PLATFORM"

# ── Check: git ────────────────────────────────────────────────────────────────
if ! command -v git &>/dev/null; then
  warn "git ist nicht installiert."
  if [ "$PLATFORM" = "Linux" ]; then
    info "Installiere git..."
    if command -v apt-get &>/dev/null; then
      sudo apt-get update -qq && sudo apt-get install -y -qq git
    elif command -v yum &>/dev/null; then
      sudo yum install -y -q git
    elif command -v dnf &>/dev/null; then
      sudo dnf install -y -q git
    else
      fail "Kein bekannter Paketmanager gefunden. Bitte git manuell installieren."
    fi
  else
    fail "Bitte git installieren: https://git-scm.com  (oder: xcode-select --install)"
  fi
fi
ok "git: $(git --version)"

# ── Check: docker ─────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  warn "Docker ist nicht installiert."
  if [ "$PLATFORM" = "Linux" ]; then
    info "Installiere Docker..."
    if command -v apt-get &>/dev/null; then
      sudo apt-get update -qq && sudo apt-get install -y -qq docker.io
      sudo systemctl enable docker --now 2>/dev/null || true
    else
      fail "Bitte Docker manuell installieren: https://docs.docker.com/engine/install/"
    fi
  else
    fail "Bitte Docker Desktop installieren: https://www.docker.com/products/docker-desktop/"
  fi
fi

if ! docker info &>/dev/null; then
  fail "Docker läuft nicht. Bitte Docker starten und erneut versuchen."
fi
ok "Docker: $(docker --version | awk '{print $3}' | tr -d ',')"

# ── Clone repo ────────────────────────────────────────────────────────────────
echo ""
if [ -d "$INSTALL_DIR" ]; then
  warn "Ordner '$INSTALL_DIR' existiert bereits — wird übersprungen (kein erneutes Klonen)."
else
  info "Repository klonen..."
  git clone "$REPO_URL" "$INSTALL_DIR"
  ok "Geklont nach ./$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# ── Build Docker image ────────────────────────────────────────────────────────
echo ""
info "Docker-Image bauen (das dauert beim ersten Mal 3–5 Minuten)..."
docker build -t "$IMAGE_NAME" .
ok "Image gebaut: $IMAGE_NAME"

# ── Stop existing container if running ───────────────────────────────────────
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  info "Bestehenden Container entfernen..."
  docker stop "$CONTAINER_NAME" 2>/dev/null || true
  docker rm   "$CONTAINER_NAME" 2>/dev/null || true
fi

# ── Start container ───────────────────────────────────────────────────────────
info "Container starten..."
docker run -d \
  --name "$CONTAINER_NAME" \
  -p "$PORT":5000 \
  -v "$VOLUME":/app/data \
  --restart unless-stopped \
  "$IMAGE_NAME"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}✓ Installation abgeschlossen!${NC}"
echo ""

# Determine access URL
if [ "$PLATFORM" = "macOS" ]; then
  ACCESS_URL="http://localhost:$PORT"
else
  # Try to get public IP, fall back to localhost
  PUBLIC_IP=$(curl -sf --max-time 3 https://api.ipify.org 2>/dev/null || echo "")
  if [ -n "$PUBLIC_IP" ]; then
    ACCESS_URL="http://$PUBLIC_IP:$PORT"
  else
    ACCESS_URL="http://localhost:$PORT"
  fi
fi

echo -e "  ${BOLD}Aufruf:${NC}  $ACCESS_URL"
echo ""
echo "  Nächster Schritt: API-Key bei openrouter.ai erstellen und"
echo "  in den Einstellungen (⚙) eintragen."
echo ""
echo "  Update später:  cd $INSTALL_DIR && bash update.sh"
echo ""
