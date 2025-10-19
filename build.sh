#!/bin/bash
# build.sh: Build with both 'latest' and 8-char commit tag

IMAGE_NAME="sorld0603/wol-dashboard"
COMMIT_ID=$(git rev-parse --short=8 HEAD 2>/dev/null || echo "manualbuild")
TAG1="latest"
TAG2="${COMMIT_ID}"

echo "🔹 Building Docker image with tags: ${TAG1}, ${TAG2}"
docker build -t ${IMAGE_NAME}:${TAG1} -t ${IMAGE_NAME}:${TAG2} .

echo "✅ Built: ${IMAGE_NAME}:${TAG1} and ${IMAGE_NAME}:${TAG2}"
