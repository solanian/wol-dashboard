IMAGE_NAME="sorld0603/wol-dashboard"
COMMIT_ID=$(git rev-parse --short=8 HEAD 2>/dev/null || echo "manualbuild")
TAG1="latest"
TAG2="${COMMIT_ID}"

echo "🔹 Pushing both tags to registry..."
docker push ${IMAGE_NAME}:${TAG1}
docker push ${IMAGE_NAME}:${TAG2}

echo "✅ Push complete for: ${IMAGE_NAME}:${TAG1} and ${IMAGE_NAME}:${TAG2}"