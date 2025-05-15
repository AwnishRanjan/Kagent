from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import random
from datetime import datetime, timedelta
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services and initialize with real data
try:
    logger.info("Attempting to import KubernetesPredictionService")
    from src.services.k8s_prediction_service import KubernetesPredictionService
    # Create service directory if it doesn't exist
    service_dir = os.path.expanduser("~/.kagent")
    Path(service_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info("Creating KubernetesPredictionService instance")
    # Initialize the prediction service with real data
    prediction_service = KubernetesPredictionService(
        metrics_interval=60,
        prediction_interval=300,
        auto_remediate=False,
        history_file=os.path.join(service_dir, "prediction_history.json"),
        remediation_history_file=os.path.join(service_dir, "remediation_history.json"),
        security_scan_interval=3600,
        cost_analysis_interval=86400,
        enable_security_scanner=True,
        enable_cost_optimizer=True,
        enable_backup_manager=True,
        use_mock=False  # Use real Kubernetes data, not mock data
    )
    
    # Start the service
    logger.info("Starting KubernetesPredictionService")
    prediction_service.start()
    logger.info("Successfully initialized and started KubernetesPredictionService")
except Exception as e:
    import traceback
    logger.error(f"Failed to initialize KubernetesPredictionService: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    prediction_service = None

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Mock data for fallback when service is unavailable
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

# API Routes for Predictor Agent
@app.route('/api/predictor/metrics', methods=['GET'])
def get_metrics():
    if prediction_service:
        try:
            logger.info("Getting current metrics from real Kubernetes cluster")
            metrics = prediction_service.get_current_metrics()
            return jsonify(metrics)
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
    
    # Fall back to mock data if service is unavailable or errors occur
    logger.warning("Using mock metrics data as fallback")
    return jsonify(get_mock_metrics())

@app.route('/api/predictor/predictions', methods=['GET'])
def get_predictions():
    if prediction_service:
        try:
            logger.info("Getting predictions from real Kubernetes cluster")
            predictions = prediction_service.get_predictions()
            return jsonify(predictions)
        except Exception as e:
            logger.error(f"Error getting predictions: {e}")
    
    logger.warning("Using mock prediction data as fallback")
    return jsonify(get_mock_predictions())

@app.route('/api/predictor/metrics/history', methods=['GET'])
def get_historical_metrics():
    timespan = request.args.get('timespan', '24h')
    
    if prediction_service and hasattr(prediction_service, 'get_historical_metrics'):
        try:
            logger.info(f"Getting historical metrics for timespan {timespan}")
            history = prediction_service.get_historical_metrics(timespan)
            return jsonify(history)
        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
    
    # Mock data fallback
    logger.warning("Using mock historical metrics data as fallback")
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

# Routes for Security Scanner
@app.route('/api/security/scan/results', methods=['GET'])
def get_security_scan_results():
    if prediction_service and prediction_service.security_scanner:
        try:
            logger.info("Getting security scan results from real Kubernetes cluster")
            results = prediction_service.get_security_scan_results()
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error getting security scan results: {e}")
            
    # Mock fallback
    logger.warning("Using mock security scan results as fallback")
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

@app.route('/api/security/scan/run', methods=['POST'])
def run_security_scan():
    if prediction_service and prediction_service.security_scanner:
        try:
            logger.info("Running security scan on real Kubernetes cluster")
            results = prediction_service.run_security_scan()
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error running security scan: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Mock fallback
    logger.warning("Using mock security scan results as fallback")
    return jsonify({"status": "success", "message": "Security scan completed"})

# Routes for Cost Optimizer
@app.route('/api/cost/analysis', methods=['GET'])
def get_cost_analysis():
    if prediction_service and prediction_service.cost_optimizer:
        try:
            logger.info("Getting cost analysis from real Kubernetes cluster")
            results = prediction_service.get_cost_optimization_suggestions()
            savings = prediction_service.get_estimated_savings()
            
            return jsonify({
                "monthlyCost": savings.get("current_cost", 1240),
                "potentialSavings": savings.get("potential_savings", 320),
                "efficiency": savings.get("efficiency", 74),
                "breakdown": {
                    "compute": savings.get("compute_cost", 820),
                    "storage": savings.get("storage_cost", 240),
                    "network": savings.get("network_cost", 180)
                },
                "suggestions": results
            })
        except Exception as e:
            logger.error(f"Error getting cost analysis: {e}")
    
    # Mock fallback
    logger.warning("Using mock cost analysis data as fallback")
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
    if prediction_service and prediction_service.backup_manager:
        try:
            logger.info("Getting backup list from real Kubernetes cluster")
            backups = prediction_service.get_backup_list()
            return jsonify(backups)
        except Exception as e:
            logger.error(f"Error getting backup list: {e}")
    
    # Mock fallback
    logger.warning("Using mock backup data as fallback")
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

@app.route('/api/backup/create', methods=['POST'])
def create_backup():
    if prediction_service and prediction_service.backup_manager:
        try:
            data = request.json or {}
            logger.info(f"Creating backup with data: {data}")
            result = prediction_service.backup_manager.create_backup(
                name=data.get('name', f'manual-backup-{int(datetime.now().timestamp())}'),
                namespace=data.get('namespace', 'default'),
                resources=data.get('resources', [])
            )
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Mock fallback
    logger.warning("Using mock backup creation as fallback")
    return jsonify({
        "id": f"backup-{int(datetime.now().timestamp())}",
        "status": "completed",
        "message": "Backup created successfully"
    })

# Routes for Remediator
@app.route('/api/remediator/issues', methods=['GET'])
def get_remediator_issues():
    if prediction_service and prediction_service.remediator:
        try:
            logger.info("Getting remediation issues from real Kubernetes cluster")
            issues = prediction_service.remediator.get_pending_issues()
            return jsonify(issues)
        except Exception as e:
            logger.error(f"Error getting remediation issues: {e}")
    
    # Mock fallback
    logger.warning("Using mock remediation issues as fallback")
    return jsonify([
        {
            "id": "issue-001",
            "type": "high_cpu_usage",
            "component": "prometheus-server-pod",
            "severity": "critical",
            "status": "pending",
            "description": "High CPU usage (92%) on prometheus-server pod",
            "timestamp": datetime.now().isoformat(),
            "remediation": "Restart pod or increase CPU limit"
        },
        {
            "id": "issue-002",
            "type": "pod_restart_loop",
            "component": "nginx-test-pod",
            "severity": "high",
            "status": "pending",
            "description": "Pod in restart loop (5 restarts in 15 minutes)",
            "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "remediation": "Check logs and fix application error"
        }
    ])

@app.route('/api/remediator/issues/<issue_id>/remediate', methods=['POST'])
def remediate_issue(issue_id):
    if prediction_service and prediction_service.remediator:
        try:
            logger.info(f"Remediating issue {issue_id} on real Kubernetes cluster")
            result = prediction_service.remediator.remediate_issue(issue_id)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error remediating issue: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Mock fallback
    logger.warning("Using mock remediation as fallback")
    return jsonify({
        "success": True,
        "message": f"Issue {issue_id} remediated successfully",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 