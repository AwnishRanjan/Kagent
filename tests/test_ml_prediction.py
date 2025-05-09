#!/usr/bin/env python3
"""
Test script for ML prediction functionality in KubernetesPredictor
"""

import os
import sys
import joblib
import numpy as np
import logging
from datetime import datetime

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import the predictor module
from agents.predictor import KubernetesPredictor, ClusterMetrics

def main():
    """Test the ML-based prediction functionality"""
    logger.info("Starting ML-based prediction test")
    
    # Path to the trained model
    model_path = os.path.abspath("model.joblib")
    logger.info(f"Using model at: {model_path}")
    
    # Check if the model file exists
    if not os.path.exists(model_path):
        logger.error(f"Model file not found at {model_path}")
        return
    
    # Initialize the predictor with the trained model
    predictor = KubernetesPredictor(
        model_path=model_path,
        threshold_config={
            "cpu_usage_critical": 90.0,
            "cpu_usage_warning": 80.0,
            "memory_usage_critical": 90.0,
            "memory_usage_warning": 80.0,
            "pod_restart_threshold": 5,
            "disk_pressure_weight": 0.8,
            "memory_pressure_weight": 0.9,
            "pid_pressure_weight": 0.7,
            "network_io_threshold": 1000000,
            "prediction_window": 3600,
            "trend_window": 1800,
            "correlation_threshold": 0.7,
            "anomaly_contamination": 0.1,
        }
    )
    logger.info("Initialized KubernetesPredictor with trained model")
    
    # Generate sample metrics
    # Normal case
    normal_metrics = ClusterMetrics(
        cpu_usage={"node-1": 50.0, "node-2": 55.0},
        memory_usage={"node-1": 60.0, "node-2": 58.0},
        pod_restarts={"pod-1": 0, "pod-2": 1},
        pod_status={"pod-1": "Running", "pod-2": "Running"},
        node_status={"node-1": "Ready", "node-2": "Ready"},
        disk_pressure={"node-1": False, "node-2": False},
        memory_pressure={"node-1": False, "node-2": False},
        pid_pressure={"node-1": False, "node-2": False},
        network_io={"node-1": {"in": 1000, "out": 2000}, "node-2": {"in": 1500, "out": 2500}},
        timestamp=datetime.now().isoformat()
    )
    
    # Anomalous case
    anomalous_metrics = ClusterMetrics(
        cpu_usage={"node-1": 95.0, "node-2": 92.0},  # High CPU usage
        memory_usage={"node-1": 94.0, "node-2": 91.0},  # High memory usage
        pod_restarts={"pod-1": 10, "pod-2": 1},  # High restart count
        pod_status={"pod-1": "CrashLoopBackOff", "pod-2": "Running"},
        node_status={"node-1": "Ready", "node-2": "Ready"},
        disk_pressure={"node-1": True, "node-2": False},  # Disk pressure
        memory_pressure={"node-1": True, "node-2": False},  # Memory pressure
        pid_pressure={"node-1": False, "node-2": False},
        network_io={"node-1": {"in": 10000, "out": 20000}, "node-2": {"in": 1500, "out": 2500}},
        timestamp=datetime.now().isoformat()
    )
    
    # Test predictions on normal metrics
    logger.info("Testing prediction on normal metrics")
    normal_result = predictor.analyze_metrics(normal_metrics.model_dump())
    
    print("==== Normal Metrics Prediction ====")
    print(f"Confidence: {normal_result.confidence:.2f}")
    print(f"Issues found: {len(normal_result.issues)}")
    for issue in normal_result.issues:
        print(f"  - {issue['type']} on {issue['component']}: {issue['description']}")
    print(f"Remediation suggestions: {len(normal_result.remediation_suggestions)}")
    
    # Test predictions on anomalous metrics
    logger.info("Testing prediction on anomalous metrics")
    anomalous_result = predictor.analyze_metrics(anomalous_metrics.model_dump())
    
    print("\n==== Anomalous Metrics Prediction ====")
    print(f"Confidence: {anomalous_result.confidence:.2f}")
    print(f"Issues found: {len(anomalous_result.issues)}")
    for issue in anomalous_result.issues:
        print(f"  - {issue['type']} on {issue['component']}: {issue['description']}")
    print(f"Remediation suggestions: {len(anomalous_result.remediation_suggestions)}")
    for suggestion in anomalous_result.remediation_suggestions:
        print(f"  - {suggestion['type']} for {suggestion['component']}: {suggestion['description']}")
    
    # Check for ML-specific predictions
    ml_issues = [issue for issue in anomalous_result.issues if issue['type'] == 'ml_anomaly']
    print(f"\nML-specific anomalies detected: {len(ml_issues)}")
    for issue in ml_issues:
        print(f"  - {issue['description']}")
    
    logger.info("ML-based prediction test completed")

if __name__ == "__main__":
    main() 