#!/usr/bin/env bash
set -euo pipefail
cd /home/pi/docker/astromanager/compose
docker compose build --no-cache web-ui pipeline-runner
docker compose up -d web-ui
