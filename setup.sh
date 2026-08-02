#!/usr/bin/env bash
# One-time setup. Needs internet; everything afterwards works offline.
#
#   ./setup.sh
#   kubectl apply -f k8s/fundex.yaml
set -euo pipefail

cd "$(dirname "$0")"

TAG=1.0
OUR_IMAGES=(auth-service employee-service director-service)
BASE_IMAGES=(python:3.12-slim mysql:8 mongo:7 redis:7-alpine trufflesuite/ganache:latest)

echo "==> Pulling third-party images"
for image in "${BASE_IMAGES[@]}"; do
    docker pull "$image"
done

echo
echo "==> Building service images"
docker build -t "auth-service:$TAG" auth-service/
docker build -t "employee-service:$TAG" employee-service/
docker build -t "director-service:$TAG" director-service/

echo
CONTEXT=$(kubectl config current-context 2>/dev/null || true)

if [ -z "$CONTEXT" ]; then
    echo "==> No Kubernetes context found."
    echo "    Enable it in Docker Desktop: Settings -> Kubernetes -> Enable Kubernetes"
    echo "    (needs internet the first time), then run this script again."
    exit 1
fi

echo "==> Kubernetes context: $CONTEXT"

case "$CONTEXT" in
    minikube)
        echo "    minikube uses its own image store; loading images into it"
        for image in "${OUR_IMAGES[@]}"; do
            minikube image load "$image:$TAG"
        done
        for image in "${BASE_IMAGES[@]}"; do
            minikube image load "$image"
        done
        HOST=$(minikube ip)
        ;;
    kind-*)
        CLUSTER=${CONTEXT#kind-}
        echo "    kind uses its own image store; loading images into cluster '$CLUSTER'"
        for image in "${OUR_IMAGES[@]}"; do
            kind load docker-image "$image:$TAG" --name "$CLUSTER"
        done
        for image in "${BASE_IMAGES[@]}"; do
            kind load docker-image "$image" --name "$CLUSTER"
        done
        HOST=127.0.0.1
        ;;
    *)
        echo "    shares the Docker daemon; no image loading needed"
        HOST=127.0.0.1
        ;;
esac

echo
echo "==> Done. Start the system with:"
echo "      kubectl apply -f k8s/fundex.yaml"
echo
echo "    Once the pods are running, the grader reaches the services at:"
echo "      --authentication-url http://$HOST:30000"
echo "      --employee-url       http://$HOST:30001"
echo "      --director-url       http://$HOST:30002"
echo "      --provider-url       http://$HOST:30003"
