# Kagent: Step-by-Step Execution Guide

This guide provides detailed instructions for running and testing the Kagent Kubernetes management system.

## Prerequisites

Make sure you have the following installed:

- Docker
- kubectl
- kind (Kubernetes in Docker)
- Helm
- Python 3.8+

## Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Make sure Kubernetes tools are installed
which kubectl kind helm
```

## Step 2: Train the ML Model

```bash
# Train the machine learning model for prediction
python tests/train_model.py

# Verify that model.joblib was created
ls -la model.joblib
```

## Step 3: Run Unit Tests

```bash
# Run the basic unit tests (no Kubernetes cluster needed)
python tests/test_all_agents.py
```

## Step 4: Set Up a Local Kubernetes Cluster

```bash
# Create a Kubernetes cluster using kind
kind create cluster --name kagent-cluster --config tests/kind-cluster.yaml

# Check that the cluster is up and running
kubectl get nodes
```

## Step 5: Deploy Test Resources

```bash
# Deploy a test nginx application
kubectl apply -f tests/test-deployment.yaml

# Install Prometheus for metrics collection
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus

# Wait for all pods to be running
kubectl get pods --watch
```

## Step 6: Generate Cluster Load

```bash
# Run the stress test to generate load on the cluster
python tests/stress_test.py
```

## Step 7: Run Comprehensive Tests on Real Cluster

```bash
# Run all agent tests against the real cluster
python tests/real_test_all_agents.py
```

## Step 8: Manually Testing Individual Agents

### Predictor Agent

```bash
# Test the predictor agent specifically
python -c "from tests.test_ml_prediction import main; main()"
```

### Security Scanner Agent

```bash
# Run just the security scanner test
python -c "from tests.test_all_agents import test_security_scanner; test_security_scanner()"
```

### Cost Optimizer Agent

```bash
# Run just the cost optimizer test
python -c "from tests.test_all_agents import test_cost_optimizer; test_cost_optimizer()"
```

### Backup and Restore

```bash
# Test backup and restore functionality
python -c "from tests.test_all_agents import test_backup_restore; test_backup_restore()"
```

### Remediator Agent

```bash
# Test the remediator agent
python -c "from tests.test_all_agents import test_remediator; test_remediator()"
```

## Step 9: Clean Up

```bash
# Delete the kind cluster when done
kind delete cluster --name kagent-cluster

# Remove any temporary files
rm -rf ~/.kagent/test_backups
```

## Troubleshooting

If you encounter any issues:

1. Make sure all Python dependencies are installed
2. Check that the model.joblib file exists in the correct location
3. Verify your Kubernetes cluster is running properly: `kubectl cluster-info`
4. Examine detailed logs: `kubectl logs <pod-name>`

For more information, refer to the documentation in the `docs/` directory. 