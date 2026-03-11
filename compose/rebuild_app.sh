#!/usr/bin/env bash
set -euo pipefail

cd /home/pi/docker/astromanager

echo "[INFO] baue Runner und Web gegen vorhandenes Base-Image"
docker compose -f compose/docker-compose.yml build astromanager-runner astromanager-web

echo "[INFO] starte Container neu"
docker compose -f compose/docker-compose.yml up -d --force-recreate astromanager-runner astromanager-web

echo "[OK] App-Container neu gebaut und gestartet"
