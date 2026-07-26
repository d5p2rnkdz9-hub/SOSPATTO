#!/usr/bin/env bash
# Avvia il piano interattivo in localhost.
# Uso:  ./serve.sh [porta]     (default: 8080)
set -euo pipefail
cd "$(dirname "$0")"
PORT="${1:-8080}"
echo ""
echo "  Piano promozione — ciclo di incontri sulla mitologia"
echo "  In ascolto su:  http://localhost:${PORT}"
echo "  (Ctrl+C per fermare)"
echo ""
if command -v python3 >/dev/null 2>&1; then
  exec python3 -m http.server "$PORT" --bind 127.0.0.1
elif command -v python >/dev/null 2>&1; then
  exec python -m http.server "$PORT" --bind 127.0.0.1
elif command -v npx >/dev/null 2>&1; then
  exec npx --yes serve -l "$PORT" .
else
  echo "Serve Python 3 o Node.js. In alternativa apri direttamente index.html nel browser."
  exit 1
fi
