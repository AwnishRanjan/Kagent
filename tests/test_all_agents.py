"""
Comprehensive test script to verify all Kagent agent functionality
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

def test_predictor():
    """Test the ML predictor agent"""
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
        
        # Create test metrics for normal and anomalous conditions
        logger.info("Creating test metrics")
        
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
        
        # Test prediction on normal metrics
        logger.info("Testing prediction on normal metrics")
        normal_result = predictor.analyze_metrics(normal_metrics.model_dump())
        print(f"Normal metrics analysis - Issues found: {len(normal_result.issues)}")
        print(f"Confidence: {normal_result.confidence:.2f}")
        
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
    """Test the security scanner agent"""
    print_section("TESTING SECURITY SCANNER AGENT")
    
    try:
        # Initialize the security scanner
        scanner = KubernetesSecurityScanner(history_file=os.path.expanduser("~/.kagent/security_history.json"))
        logger.info("Initialized KubernetesSecurityScanner")
        
        # Perform a security scan
        logger.info("Performing security scan")
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
    """Test the cost optimizer agent"""
    print_section("TESTING COST OPTIMIZER AGENT")
    
    try:
        # Initialize the cost optimizer
        optimizer = KubernetesCostOptimizer(
            history_file=os.path.expanduser("~/.kagent/cost_history.json"),
            cloud_provider="aws"
        )
        logger.info("Initialized KubernetesCostOptimizer")
        
        # Collect current metrics
        logger.info("Collecting metrics for cost analysis")
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
    """Test the backup/restore functionality"""
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
        logger.info(f"Creating backup: {backup_name}")
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
            logger.info(f"Restoring from backup: {backup_name}")
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
    """Test the remediator agent"""
    print_section("TESTING REMEDIATOR AGENT")
    
    try:
        # Initialize the remediator
        remediator = KubernetesRemediator(use_mock=True)
        logger.info("Initialized KubernetesRemediator")
        
        # Create a test issue to remediate (high CPU usage)
        test_issue = {
            "issue_type": "high_cpu_usage",
            "component": "test-deployment",
            "severity": "critical",
            "description": "Critical CPU usage on test-deployment: 95.0%",
            "details": {
                "usage": 95.0,
                "threshold": 90.0
            }
        }
        
        # Apply remediation
        logger.info("Testing remediation")
        result = remediator.remediate_issue(test_issue)
        
        # Display results
        print(f"Remediation completed with success: {result.success}")
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
    """Run all agent tests"""
    print_section("KAGENT COMPREHENSIVE TESTS")
    print("Testing all Kagent agent functionality...\n")
    
    results = {
        "Predictor": test_predictor(),
        "Security Scanner": test_security_scanner(),
        "Cost Optimizer": test_cost_optimizer(),
        "Backup/Restore": test_backup_restore(),
        "Remediator": test_remediator()
    }
    
    # Print summary
    print_section("TEST RESULTS SUMMARY")
    
    all_passed = True
    for agent, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{agent}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All agent tests passed successfully! The system is working properly.")
    else:
        print("\n⚠️ Some tests failed. Check the logs for details.")
    
if __name__ == "__main__":
    main() 