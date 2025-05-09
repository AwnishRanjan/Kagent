# Kagent Tests

This directory contains test files for the Kagent project:

## Test Files

- `test_all_agents.py` - Comprehensive test script for all Kagent agents
- `real_test_all_agents.py` - Tests all agents on a real Kubernetes cluster
- `test_ml_prediction.py` - Tests for ML prediction functionality
- `train_model.py` - Script to train a machine learning model for testing
- `stress_test.py` - Utility to generate load on a Kubernetes cluster
- `kind-cluster.yaml` - Configuration for setting up a test Kubernetes cluster
- `test-deployment.yaml` - Sample deployment for testing

## Running Tests

To run tests on a real Kubernetes cluster:

1. Create a test cluster:
   ```
   kind create cluster --name kagent-cluster --config tests/kind-cluster.yaml
   ```

2. Deploy test resources:
   ```
   kubectl apply -f tests/test-deployment.yaml
   ```

3. Run the tests:
   ```
   python tests/real_test_all_agents.py
   ```

4. Clean up:
   ```
   kind delete cluster --name kagent-cluster
   ``` 