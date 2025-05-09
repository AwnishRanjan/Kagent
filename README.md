# Kagent: AI-powered Kubernetes Management Platform

Kagent is a comprehensive Kubernetes management platform that uses AI and machine learning to monitor, predict, remediate, secure, optimize, and backup Kubernetes clusters.

## Features

- **Predictor Agent**: Uses machine learning to predict potential issues before they occur
- **Security Scanner**: Scans for vulnerabilities, misconfigurations, and compliance issues
- **Cost Optimizer**: Analyzes cluster for cost optimization opportunities
- **Backup Manager**: Automated backup and restore of Kubernetes resources
- **Remediator**: Automated remediation of detected issues
- **Modern Web UI**: Clean, responsive dashboard for monitoring and management

## Architecture

Kagent consists of several components:

- **Python Backend**: Core agents for cluster interaction and AI processing
- **React Frontend**: Modern web interface for visualization and management
- **Machine Learning Models**: Trained to detect anomalies and predict issues
- **Kubernetes Integration**: Deep integration with Kubernetes API

## Getting Started

### Prerequisites

- Python 3.8+
- Kubernetes cluster (a local cluster using kind works for testing)
- Docker
- Node.js and npm (for the frontend)

### Backend Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Train the ML model:
   ```bash
   python tests/train_model.py
   ```

3. Test the agents:
   ```bash
   python tests/test_all_agents.py
   ```

### Running on a Real Kubernetes Cluster

Follow these steps to test all functionality on a real Kubernetes cluster:

1. Create a test cluster:
   ```bash
   kind create cluster --name kagent-cluster --config tests/kind-cluster.yaml
   ```

2. Deploy test resources:
   ```bash
   kubectl apply -f tests/test-deployment.yaml
   ```

3. Install metrics collection:
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   helm install prometheus prometheus-community/prometheus
   ```

4. Run the comprehensive tests:
   ```bash
   python tests/real_test_all_agents.py
   ```

### Frontend Setup

1. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

3. Access the dashboard at [http://localhost:3000](http://localhost:3000)

## Project Structure

```
kagent/
├── agents/              # Core AI agents
├── frontend/            # React frontend
├── src/                 # Backend source code
├── tests/               # Test scripts and utilities
│   ├── test_all_agents.py
│   ├── real_test_all_agents.py
│   ├── train_model.py
│   └── ...
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Running Kagent

For convenience, we provide scripts to run Kagent:

- `./run_kagent.sh`: Run all agents on a test Kubernetes cluster
- `./setup_frontend.sh`: Set up and run the frontend

## Screenshots

![Dashboard](https://example.com/dashboard.png)
![ML Predictor](https://example.com/predictor.png)
![Security Scanner](https://example.com/security.png)

## License

MIT 