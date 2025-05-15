#!/bin/bash

# Build Docker images
echo "Building Docker images..."
docker build -t kagent-backend:latest -f k8s/Dockerfile.backend .
docker build -t kagent-frontend:latest -f k8s/Dockerfile.frontend .

# Load images into kind cluster (if using kind)
# kind load docker-image kagent-backend:latest
# kind load docker-image kagent-frontend:latest

# Apply Kubernetes manifests
echo "Deploying to Kubernetes..."
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/kagent-backend
kubectl wait --for=condition=available --timeout=300s deployment/kagent-frontend

echo "Deployment complete!"
echo "Frontend service will be available at:"
kubectl get service kagent-frontend -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 