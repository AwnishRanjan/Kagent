#!/bin/bash
# Kagent execution script
# This script runs all the essential steps to test Kagent on a local Kubernetes cluster

set -e  # Exit on error

echo "=== KAGENT EXECUTION SCRIPT ==="
echo "This script will set up and test Kagent on a local Kubernetes cluster"

# Step 1: Check prerequisites
echo -e "\n=== Step 1: Checking prerequisites ==="
which kubectl kind helm python || { echo "Error: Missing required tools"; exit 1; }

# Step 2: Train the ML model
echo -e "\n=== Step 2: Training ML model ==="
python tests/train_model.py

# Step 3: Create Kubernetes cluster
echo -e "\n=== Step 3: Creating Kubernetes cluster ==="
kind create cluster --name kagent-cluster --config tests/kind-cluster.yaml

echo "Waiting for cluster to be ready..."
sleep 10
kubectl get nodes

# Step 4: Deploy test resources
echo -e "\n=== Step 4: Deploying test resources ==="
kubectl apply -f tests/test-deployment.yaml

echo "Installing Prometheus..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus

echo "Waiting for resources to be ready..."
kubectl get pods
sleep 15

# Step 5: Generate load
echo -e "\n=== Step 5: Generating cluster load ==="
python tests/stress_test.py

# Step 6: Run tests
echo -e "\n=== Step 6: Running Kagent tests ==="
python tests/real_test_all_agents.py

# Step 7: Clean up
echo -e "\n=== Step 7: Cleaning up ==="
read -p "Do you want to delete the cluster now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kind delete cluster --name kagent-cluster
    echo "Cluster deleted"
else
    echo "Cluster not deleted. You can manually delete it later with:"
    echo "kind delete cluster --name kagent-cluster"
fi

echo -e "\n=== KAGENT EXECUTION COMPLETED ===" 