#!/bin/bash
# Serve the whole project root so /web/ can fetch ../app/src/main/assets/*.json
cd "$(dirname "$0")/.."
PORT="${1:-8000}"
echo "Englive Web → http://localhost:$PORT/web/"
python3 -m http.server "$PORT"
