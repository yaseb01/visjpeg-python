#!/usr/bin/env bash
set -e

PORT="${1:-8501}"

echo "Baue VisJPEG Docker-Image..."
docker build -t visjpeg .

echo ""
echo "Starte VisJPEG auf http://localhost:${PORT}"
echo "Druecke Ctrl+C zum Beenden."
echo ""

docker run --rm -it -p "${PORT}:8501" -v "$(pwd)/visjpeg:/app/visjpeg:ro" visjpeg
