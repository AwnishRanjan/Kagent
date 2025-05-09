from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import random
from datetime import datetime, timedelta
import os

# Import services
try:
    from src.services.k8s_prediction_service import K8sPredictionService
    prediction_service = K8sPredictionService()
except ImportError:
    prediction_service = None
    print("Warning: K8sPredictionService not available")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Mock data for development (will be replaced by actual service calls)
def get_mock_metrics():
    return {
        "nodes": {
            "kagent-cluster-control-plane": {
                "cpu_usage": random.randint(30, 70),
                "memory_usage": random.randint(40, 60),
                "status": "Ready",
                "disk_pressure": False,
                "memory_pressure": False,
                "pid_pressure": False,
                "network_io": {"in": random.randint(2000, 6000), "out": random.randint(3000, 7000)}
            },
            "kagent-cluster-worker": {
                "cpu_usage": random.randint(30, 70),
                "memory_usage": random.randint(40, 60),
                "status": "Ready",
                "disk_pressure": False,
                "memory_pressure": False,
                "pid_pressure": False,
                "network_io": {"in": random.randint(2000, 6000), "out": random.randint(3000, 7000)}
            }
        },
        "pods": {
            "nginx-test-7f8bcbcf44-clbk2": {
                "status": "Running",
                "restarts": 0,
                "cpu_usage": random.randint(10, 20),
                "memory_usage": random.randint(30, 40)
            },
            "prometheus-server-7687845bbc-8g4tb": {
                "status": "Running",
                "restarts": 2,
                "cpu_usage": random.randint(60, 80),
                "memory_usage": random.randint(70, 90)
            }
        },
        "timestamp": datetime.now().isoformat()
    }

def get_mock_predictions():
    return {
        "issues": [
            {
                "id": 1,
                "type": "high_cpu_usage",
                "component": "prometheus-server-7687845bbc-8g4tb",
                "severity": "warning",
                "description": "High CPU usage on prometheus-server pod: 67%",
                "details": {
                    "usage": 67,
                    "threshold": 65
                },
                "timestamp": (datetime.now() - timedelta(minutes=5)).timestamp() * 1000
            },
            {
                "id": 2,
                "type": "high_memory_usage",
                "component": "prometheus-server-7687845bbc-8g4tb",
                "severity": "warning",
                "description": "High memory usage on prometheus-server pod: 78%",
                "details": {
                    "usage": 78,
                    "threshold": 75
                },
                "timestamp": (datetime.now() - timedelta(minutes=5)).timestamp() * 1000
            }
        ],
        "remediation_suggestions": [
            {
                "id": 1,
                "issue_id": 1,
                "type": "scale_resources",
                "component": "prometheus-server-7687845bbc-8g4tb",
                "description": "Increase CPU limit for prometheus-server deployment",
                "steps": ["Increase CPU limit to 300m", "Apply changes with kubectl"]
            }
        ],
        "confidence": 0.87,
        "ml_model_used": True,
        "model_info": {
            "name": "isolation_forest",
            "version": "1.0.0",
            "training_date": datetime.now().isoformat(),
            "accuracy": 0.92
        }
    }

def get_mock_model_info():
    return {
        "name": "IsolationForest",
        "version": "1.0.0",
        "trained_at": datetime.now().isoformat(),
        "accuracy": 0.92,
        "features": ["cpu_usage", "memory_usage", "pod_restarts", "network_io"],
        "parameters": {
            "n_estimators": 100,
            "contamination": 0.1,
            "random_state": 42
        }
    }

# API Routes for Predictor Agent
@app.route('/api/predictor/metrics', methods=['GET'])
def get_metrics():
    if prediction_service:
        try:
            metrics = prediction_service.get_current_metrics()
            return jsonify(metrics)
        except Exception as e:
            print(f"Error getting metrics: {e}")
    
    # Fall back to mock data if service is unavailable or errors occur
    return jsonify(get_mock_metrics())

@app.route('/api/predictor/predictions', methods=['GET'])
def get_predictions():
    if prediction_service:
        try:
            predictions = prediction_service.get_predictions()
            return jsonify(predictions)
        except Exception as e:
            print(f"Error getting predictions: {e}")
    
    return jsonify(get_mock_predictions())

@app.route('/api/predictor/metrics/history', methods=['GET'])
def get_historical_metrics():
    timespan = request.args.get('timespan', '24h')
    # Mock data for now
    return jsonify({
        "cpu_usage": [
            {"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), "value": random.randint(20, 80)} 
            for i in range(24)
        ],
        "memory_usage": [
            {"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), "value": random.randint(30, 90)} 
            for i in range(24)
        ]
    })

@app.route('/api/predictor/model/info', methods=['GET'])
def get_model_info():
    if prediction_service and hasattr(prediction_service, 'get_model_info'):
        try:
            model_info = prediction_service.get_model_info()
            return jsonify(model_info)
        except Exception as e:
            print(f"Error getting model info: {e}")
    
    return jsonify(get_mock_model_info())

@app.route('/api/predictor/model/train', methods=['POST'])
def train_model():
    params = request.json
    if prediction_service and hasattr(prediction_service, 'train_model'):
        try:
            result = prediction_service.train_model(params)
            return jsonify(result)
        except Exception as e:
            print(f"Error training model: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Mock response
    return jsonify({
        "status": "success",
        "message": "Model training started",
        "job_id": "train_" + datetime.now().strftime("%Y%m%d%H%M%S")
    })

# Routes for Security Scanner
@app.route('/api/security/scan/results', methods=['GET'])
def get_security_scan_results():
    # Mock security scan results
    return jsonify({
        "vulnerabilities": 3,
        "misconfigurations": 12,
        "compliance_issues": 2,
        "last_scan": datetime.now().isoformat(),
        "details": {
            "critical": 1,
            "high": 2,
            "medium": 8,
            "low": 4
        }
    })

# Routes for Cost Optimizer
@app.route('/api/cost/analysis', methods=['GET'])
def get_cost_analysis():
    # Mock cost analysis
    return jsonify({
        "monthlyCost": 1240,
        "potentialSavings": 320,
        "efficiency": 74,
        "breakdown": {
            "compute": 820,
            "storage": 240,
            "network": 180
        }
    })

# Routes for Backup Manager
@app.route('/api/backup/list', methods=['GET'])
def get_backups():
    # Mock backups
    return jsonify([
        {
            "id": "backup-001",
            "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
            "resources": 42,
            "size": "156MB",
            "status": "completed"
        },
        {
            "id": "backup-002",
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
            "resources": 42,
            "size": "158MB",
            "status": "completed"
        }
    ])

# Routes for Remediator
@app.route('/api/remediator/issues', methods=['GET'])
def get_remediator_issues():
    # Mock remediator issues
    return jsonify([
        {
            "id": 1,
            "type": "high_cpu_usage",
            "component": "prometheus-server-7687845bbc-8g4tb",
            "severity": "warning",
            "description": "High CPU usage on prometheus-server pod: 67%",
            "timestamp": (datetime.now() - timedelta(minutes=5)).timestamp() * 1000
        },
        {
            "id": 2,
            "type": "high_memory_usage",
            "component": "prometheus-server-7687845bbc-8g4tb",
            "severity": "warning",
            "description": "High memory usage on prometheus-server pod: 78%",
            "timestamp": (datetime.now() - timedelta(minutes=5)).timestamp() * 1000
        }
    ])

if __name__ == '__main__':
    app.run(debug=True, port=5000) 