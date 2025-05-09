"""
Script to monitor a real Kubernetes cluster using the Kagent predictor
"""

import os
import logging
import json
import time
from pathlib import Path
from datetime import datetime
import kubernetes as k8s

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import the predictor functionality
from agents.predictor import KubernetesPredictor, ClusterMetrics

def collect_cluster_metrics():
    """Collect real metrics from a Kubernetes cluster"""
    logger.info("Collecting metrics from Kubernetes cluster")
    
    # Load kube config
    try:
        k8s.config.load_kube_config()
    except Exception as e:
        logger.error(f"Error loading kube config: {e}")
        return None
    
    # Initialize API clients
    core_api = k8s.client.CoreV1Api()
    
    try:
        # Get nodes
        nodes = core_api.list_node().items
        logger.info(f"Found {len(nodes)} nodes in the cluster")
        
        # Get pods
        pods = core_api.list_pod_for_all_namespaces().items
        logger.info(f"Found {len(pods)} pods in the cluster")
        
        # Initialize metrics dictionaries
        cpu_usage = {}
        memory_usage = {}
        pod_restarts = {}
        pod_status = {}
        node_status = {}
        disk_pressure = {}
        memory_pressure = {}
        pid_pressure = {}
        network_io = {}
        
        # Collect node metrics
        for node in nodes:
            node_name = node.metadata.name
            
            # Node status
            node_ready = False
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    node_ready = condition.status == "True"
            node_status[node_name] = "Ready" if node_ready else "NotReady"
            
            # Node pressure conditions
            disk_pressure[node_name] = False
            memory_pressure[node_name] = False
            pid_pressure[node_name] = False
            
            for condition in node.status.conditions:
                if condition.type == "DiskPressure" and condition.status == "True":
                    disk_pressure[node_name] = True
                if condition.type == "MemoryPressure" and condition.status == "True":
                    memory_pressure[node_name] = True
                if condition.type == "PIDPressure" and condition.status == "True":
                    pid_pressure[node_name] = True
            
            # Estimate CPU and memory usage (in a real system, you'd use metrics-server)
            # For this demo, we'll simulate with random values
            import random
            cpu_usage[node_name] = random.uniform(10, 85)  # Simulated CPU usage %
            memory_usage[node_name] = random.uniform(20, 75)  # Simulated memory usage %
            
            # Simulated network I/O
            network_io[node_name] = {
                "in": random.uniform(500000, 2000000),  # bytes in
                "out": random.uniform(500000, 2000000)  # bytes out
            }
        
        # Collect pod metrics
        for pod in pods:
            pod_name = pod.metadata.name
            pod_status[pod_name] = pod.status.phase
            
            # Pod restart count
            restart_count = 0
            for container_status in pod.status.container_statuses or []:
                restart_count += container_status.restart_count
            pod_restarts[pod_name] = restart_count
        
        # Create metrics object
        metrics = ClusterMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            pod_restarts=pod_restarts,
            pod_status=pod_status,
            node_status=node_status,
            disk_pressure=disk_pressure,
            memory_pressure=memory_pressure,
            pid_pressure=pid_pressure,
            network_io=network_io,
            timestamp=datetime.now().isoformat()
        )
        
        return metrics
    
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return None

def main():
    """Monitor a Kubernetes cluster using the predictor"""
    logger.info("Starting Kubernetes cluster monitoring")
    
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
    
    # Monitoring loop
    try:
        while True:
            # Collect metrics from the cluster
            metrics = collect_cluster_metrics()
            
            if metrics:
                # Analyze metrics
                logger.info("Analyzing cluster metrics")
                result = predictor.analyze_metrics(metrics.model_dump())
                
                # Display results
                print("\n==== Kubernetes Cluster Analysis ====")
                print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Confidence: {result.confidence:.2f}")
                print(f"Issues found: {len(result.issues)}")
                
                if result.issues:
                    print("\nDetected Issues:")
                    for issue in result.issues:
                        severity_indicator = "🔴" if issue['severity'] == "critical" else "🟡"
                        print(f"  {severity_indicator} {issue['type']} on {issue['component']}: {issue['description']}")
                
                if result.remediation_suggestions:
                    print("\nRemediation Suggestions:")
                    for suggestion in result.remediation_suggestions:
                        print(f"  ✅ {suggestion['type']} for {suggestion['component']}: {suggestion['description']}")
                
                # Check for ML-specific predictions
                ml_issues = [issue for issue in result.issues if issue['type'] == 'ml_anomaly']
                if ml_issues:
                    print(f"\nML-specific anomalies detected: {len(ml_issues)}")
                    for issue in ml_issues:
                        print(f"  🤖 {issue['description']}")
                
                print("\nPress Ctrl+C to exit...")
            
            # Wait before next collection
            time.sleep(60)  # Collect metrics every 60 seconds
    
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error during monitoring: {e}")

if __name__ == "__main__":
    main() 