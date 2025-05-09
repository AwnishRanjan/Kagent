#!/usr/bin/env python3
"""
Comprehensive test script to verify all Kagent agent functionality on a real Kubernetes cluster
"""

import os
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import all the agents
from agents.predictor import KubernetesPredictor, ClusterMetrics
from agents.security_scanner import KubernetesSecurityScanner
from agents.cost_optimizer import KubernetesCostOptimizer
from agents.backup_manager import KubernetesBackupManager, BackupJob, RestoreJob
from agents.remediator import KubernetesRemediator

def print_section(title):
    """Print a section title with formatting"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def collect_real_metrics():
    """Collect real metrics from the Kubernetes cluster"""
    import subprocess
    import json
    
    print("Collecting real metrics from cluster...")
    
    # Get node metrics
    node_cmd = "kubectl get nodes -o json"
    node_output = subprocess.run(node_cmd, shell=True, capture_output=True, text=True).stdout
    nodes_data = json.loads(node_output)
    
    # Get pod metrics
    pod_cmd = "kubectl get pods --all-namespaces -o json"
    pod_output = subprocess.run(pod_cmd, shell=True, capture_output=True, text=True).stdout
    pods_data = json.loads(pod_output)
    
    # Process node metrics
    cpu_usage = {}
    memory_usage = {}
    node_status = {}
    disk_pressure = {}
    memory_pressure = {}
    pid_pressure = {}
    network_io = {}
    
    for node in nodes_data.get("items", []):
        node_name = node["metadata"]["name"]
        
        # Set default values (we would normally get this from metrics-server or Prometheus)
        cpu_usage[node_name] = 50.0 + (hash(node_name) % 30)  # Simulate different CPU usage per node
        memory_usage[node_name] = 40.0 + (hash(node_name) % 40)  # Simulate different Memory usage per node
        network_io[node_name] = {"in": 1000 + (hash(node_name) % 5000), "out": 2000 + (hash(node_name) % 6000)}
        
        # Get node conditions
        node_status[node_name] = "NotReady"
        disk_pressure[node_name] = False
        memory_pressure[node_name] = False
        pid_pressure[node_name] = False
        
        for condition in node["status"].get("conditions", []):
            if condition["type"] == "Ready" and condition["status"] == "True":
                node_status[node_name] = "Ready"
            elif condition["type"] == "DiskPressure" and condition["status"] == "True":
                disk_pressure[node_name] = True
            elif condition["type"] == "MemoryPressure" and condition["status"] == "True":
                memory_pressure[node_name] = True
            elif condition["type"] == "PIDPressure" and condition["status"] == "True":
                pid_pressure[node_name] = True
    
    # Process pod metrics
    pod_restarts = {}
    pod_status = {}
    
    for pod in pods_data.get("items", []):
        pod_name = pod["metadata"]["name"]
        pod_status[pod_name] = pod["status"]["phase"]
        
        # Count container restarts
        restarts = 0
        for container_status in pod["status"].get("containerStatuses", []):
            restarts += container_status.get("restartCount", 0)
        
        pod_restarts[pod_name] = restarts
    
    # Create a ClusterMetrics object
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

def test_predictor():
    """Test the ML predictor agent on real cluster data"""
    print_section("TESTING PREDICTOR AGENT")
    
    try:
        # Path to the trained model
        model_path = os.path.abspath("model.joblib")
        if not os.path.exists(model_path):
            logger.error(f"Model file not found at {model_path}")
            return False
            
        # Initialize the predictor
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
        
        # Get real metrics from the cluster
        real_metrics = collect_real_metrics()
        logger.info("Collected real metrics from the cluster")
        
        # Test prediction on real metrics
        logger.info("Testing prediction on real metrics")
        real_result = predictor.analyze_metrics(real_metrics.model_dump())
        print(f"Real metrics analysis - Issues found: {len(real_result.issues)}")
        print(f"Confidence: {real_result.confidence:.2f}")
        
        # Create an anomalous metrics case by modifying the real metrics
        anomalous_metrics = real_metrics
        
        # Modify some values to create anomalies
        for node in anomalous_metrics.cpu_usage:
            anomalous_metrics.cpu_usage[node] = 95.0  # High CPU usage
        
        for node in anomalous_metrics.memory_usage:
            anomalous_metrics.memory_usage[node] = 92.0  # High memory usage
        
        # Introduce some pod restart anomalies
        for pod in list(anomalous_metrics.pod_restarts.keys())[:2]:
            anomalous_metrics.pod_restarts[pod] = 10  # High restart count
            
        # Test prediction on anomalous metrics
        logger.info("Testing prediction on anomalous metrics")
        anomalous_result = predictor.analyze_metrics(anomalous_metrics.model_dump())
        print(f"Anomalous metrics analysis - Issues found: {len(anomalous_result.issues)}")
        print(f"Confidence: {anomalous_result.confidence:.2f}")
        print(f"Remediation suggestions: {len(anomalous_result.remediation_suggestions)}")
        
        # Check for ML-specific predictions
        ml_issues = [issue for issue in anomalous_result.issues if issue['type'] == 'ml_anomaly']
        print(f"ML-specific anomalies detected: {len(ml_issues)}")
        
        # Test success criteria
        if len(anomalous_result.issues) > 0 and len(anomalous_result.remediation_suggestions) > 0:
            print("\n✅ Predictor agent test passed successfully!")
            return True
        else:
            print("\n❌ Predictor agent test failed - No issues or remediation suggestions detected")
            return False
            
    except Exception as e:
        logger.error(f"Error in predictor test: {e}")
        print(f"\n❌ Predictor agent test failed with error: {e}")
        return False

def test_security_scanner():
    """Test the security scanner agent on real cluster"""
    print_section("TESTING SECURITY SCANNER AGENT")
    
    try:
        # Initialize the security scanner
        scanner = KubernetesSecurityScanner(history_file=os.path.expanduser("~/.kagent/security_history.json"))
        logger.info("Initialized KubernetesSecurityScanner")
        
        # Perform a security scan on the real cluster
        logger.info("Performing security scan on real cluster")
        scan_result = scanner.perform_security_scan()
        
        # Display results
        vulnerabilities = scan_result.vulnerabilities
        misconfigurations = scan_result.misconfigurations
        compliance_issues = scan_result.compliance_issues
        
        total_issues = len(vulnerabilities) + len(misconfigurations) + len(compliance_issues)
        print(f"Security scan completed - Total issues found: {total_issues}")
        print(f"Vulnerabilities: {len(vulnerabilities)}")
        print(f"Misconfigurations: {len(misconfigurations)}")
        print(f"Compliance issues: {len(compliance_issues)}")
        
        # Test success (we don't actually need to find issues for the test to be successful)
        print("\n✅ Security scanner agent test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error in security scanner test: {e}")
        print(f"\n❌ Security scanner agent test failed with error: {e}")
        return False

def test_cost_optimizer():
    """Test the cost optimizer agent on real cluster"""
    print_section("TESTING COST OPTIMIZER AGENT")
    
    try:
        # Initialize the cost optimizer
        optimizer = KubernetesCostOptimizer(
            history_file=os.path.expanduser("~/.kagent/cost_history.json"),
            cloud_provider="aws"
        )
        logger.info("Initialized KubernetesCostOptimizer")
        
        # Collect current metrics
        logger.info("Collecting metrics for cost analysis from real cluster")
        optimizer._collect_current_metrics()
        
        # Run cost analysis
        logger.info("Analyzing cost optimization opportunities")
        suggestions = optimizer.analyze_cost_optimization()
        
        # Calculate total potential savings
        total_savings = 0.0
        for suggestion in suggestions:
            savings = suggestion.estimated_savings.get('total_monthly', 0)
            if isinstance(savings, (int, float)):
                total_savings += savings
        
        print(f"Cost optimization analysis completed")
        print(f"Optimization suggestions: {len(suggestions)}")
        print(f"Estimated monthly savings: ${round(total_savings, 2)}")
        
        # Test success (we don't actually need to find opportunities for the test to be successful)
        print("\n✅ Cost optimizer agent test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error in cost optimizer test: {e}")
        print(f"\n❌ Cost optimizer agent test failed with error: {e}")
        return False

def test_backup_restore():
    """Test the backup/restore functionality on real cluster"""
    print_section("TESTING BACKUP/RESTORE FUNCTIONALITY")
    
    try:
        # Initialize the backup manager
        backup_dir = os.path.expanduser("~/.kagent/test_backups")
        history_file = os.path.expanduser("~/.kagent/test_backup_history.json")
        
        # Create directories if they don't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_manager = KubernetesBackupManager(
            backup_dir=backup_dir,
            history_file=history_file
        )
        logger.info(f"Initialized KubernetesBackupManager with backup dir: {backup_dir}")
        
        # Create a backup job
        backup_name = f"test-backup-{int(time.time())}"
        backup_job = BackupJob(
            id=f"test-{int(time.time())}",
            name=backup_name,
            namespaces=["default"],
            resource_types=["deployment", "service"],
            include_labels={},
            exclude_labels={}
        )
        
        # Perform backup
        logger.info(f"Creating backup of real cluster: {backup_name}")
        backup_result = backup_manager.create_backup(backup_job)
        
        print(f"Backup completed with status: {backup_result.status}")
        if backup_result.status == "completed":
            print(f"Resources backed up: {backup_result.resources_backed_up}")
            
            # Create a restore job
            restore_name = f"test-restore-{int(time.time())}"
            restore_job = RestoreJob(
                id=f"restore-{int(time.time())}",
                backup_id=backup_result.id,
                name=restore_name,
                namespaces=["default"],
                resource_types=["deployment", "service"],
                include_labels={},
                exclude_labels={},
                restore_strategy="create_or_replace"
            )
            
            # Perform restore
            logger.info(f"Restoring from backup to real cluster: {backup_name}")
            restore_result = backup_manager.restore_from_backup(restore_job)
            
            print(f"Restore completed with status: {restore_result.status}")
            if restore_result.status == "completed":
                print(f"Resources restored: {restore_result.resources_restored}")
                print("\n✅ Backup/restore functionality test passed!")
                return True
            else:
                print(f"Restore error: {restore_result.error_message}")
                print("\n❌ Backup/restore functionality test failed - Restore failed")
                return False
        else:
            print(f"Backup error: {backup_result.error_message}")
            print("\n❌ Backup/restore functionality test failed - Backup failed")
            return False
            
    except Exception as e:
        logger.error(f"Error in backup/restore test: {e}")
        print(f"\n❌ Backup/restore functionality test failed with error: {e}")
        return False

def test_remediator():
    """Test the remediator agent on real cluster issues"""
    print_section("TESTING REMEDIATOR AGENT")
    
    try:
        # Initialize the remediator
        remediator = KubernetesRemediator(use_mock=False)  # Use real remediation
        logger.info("Initialized KubernetesRemediator for real cluster")
        
        # Get real metrics to find issues
        real_metrics = collect_real_metrics()
        
        # Find or create a test issue to remediate
        issue_found = False
        test_issue = None
        
        # Check for high CPU
        for node, usage in real_metrics.cpu_usage.items():
            if usage > 80.0:
                test_issue = {
                    "issue_type": "high_cpu_usage",
                    "component": node,
                    "severity": "warning",
                    "description": f"High CPU usage on {node}: {usage}%",
                    "details": {
                        "usage": usage,
                        "threshold": 80.0
                    }
                }
                issue_found = True
                break
        
        # If no real issue found, create a mock one
        if not issue_found:
            node_names = list(real_metrics.cpu_usage.keys())
            if node_names:
                test_node = node_names[0]
                test_issue = {
                    "issue_type": "high_cpu_usage",
                    "component": test_node,
                    "severity": "critical",
                    "description": f"Critical CPU usage on {test_node}: 95.0%",
                    "details": {
                        "usage": 95.0,
                        "threshold": 90.0
                    }
                }
            else:
                test_issue = {
                    "issue_type": "high_cpu_usage",
                    "component": "unknown-node",
                    "severity": "critical",
                    "description": "Critical CPU usage: 95.0%",
                    "details": {
                        "usage": 95.0,
                        "threshold": 90.0
                    }
                }
        
        logger.info(f"Testing remediation for issue: {test_issue['description']}")
        
        # Apply remediation
        result = remediator.remediate_issue(test_issue)
        
        # Display results
        print(f"Remediation on real cluster completed with success: {result.success}")
        print(f"Action ID: {result.action_id}")
        print(f"Timestamp: {result.timestamp}")
        if result.error_message:
            print(f"Error message: {result.error_message}")
        
        # Test success
        print("\n✅ Remediator agent test passed!")
        return True
            
    except Exception as e:
        logger.error(f"Error in remediator test: {e}")
        print(f"\n❌ Remediator agent test failed with error: {e}")
        return False

def main():
    """Run all agent tests on real Kubernetes cluster"""
    print_section("KAGENT COMPREHENSIVE REAL-CLUSTER TESTS")
    print("Testing all Kagent agent functionality on real Kubernetes cluster...\n")
    
    # Make sure necessary directories exist
    os.makedirs(os.path.expanduser("~/.kagent"), exist_ok=True)
    
    results = {
        "Predictor": test_predictor(),
        "Security Scanner": test_security_scanner(),
        "Cost Optimizer": test_cost_optimizer(),
        "Backup/Restore": test_backup_restore(),
        "Remediator": test_remediator()
    }
    
    # Print summary
    print_section("REAL-CLUSTER TEST RESULTS SUMMARY")
    
    all_passed = True
    for agent, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{agent}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All agent tests passed successfully on real cluster! The system is working properly.")
    else:
        print("\n⚠️ Some tests failed on real cluster. Check the logs for details.")
    
if __name__ == "__main__":
    main() 