#!/bin/bash
IMAGE_NAME="sorld0603/wol-dashboard"
TAG="latest"

echo "🔹 Pushing image to Docker Hub..."
docker push ${IMAGE_NAME}:${TAG}
echo "✅ Push complete!"
