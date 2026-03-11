#!/usr/bin/env bash
set -euo pipefail

cd /home/pi/docker/astromanager

IMAGE_NAME="astromanager-base"
IMAGE_TAG="bookworm"

echo "[INFO] baue Base-Image ${IMAGE_NAME}:${IMAGE_TAG}"
docker build -f image/Dockerfile.base -t "${IMAGE_NAME}:${IMAGE_TAG}" .

echo "[OK] Base-Image fertig: ${IMAGE_NAME}:${IMAGE_TAG}"
