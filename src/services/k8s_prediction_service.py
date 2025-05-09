"""
Kubernetes Prediction Service

This module provides a service that integrates metrics collection,
prediction, and remediation for Kubernetes clusters.
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path
import os

from ..agents.metrics_collector import KubernetesMetricsCollector
from ..agents.predictor import KubernetesPredictor
from ..agents.remediator import KubernetesRemediator
from ..agents.security_scanner import KubernetesSecurityScanner
from ..agents.cost_optimizer import KubernetesCostOptimizer
from ..agents.backup_manager import KubernetesBackupManager

logger = logging.getLogger(__name__)

class KubernetesPredictionService:
    """
    Service that integrates metrics collection, prediction, and remediation
    for Kubernetes clusters.
    
    This service:
    1. Collects metrics from the cluster at regular intervals
    2. Analyzes metrics to predict potential issues
    3. Applies remediation actions when issues are detected
    4. Maintains history of predictions and remediations
    5. Provides security scanning capabilities
    6. Offers cost optimization suggestions
    7. Supports backup and restore operations
    """
    
    def __init__(
        self,
        metrics_interval: int = 60,
        prediction_interval: int = 300,
        auto_remediate: bool = False,
        kubeconfig_path: Optional[str] = None,
        history_file: Optional[str] = None,
        remediation_history_file: Optional[str] = None,
        security_scan_interval: int = 3600,  # Every hour
        cost_analysis_interval: int = 86400,  # Every day
        enable_security_scanner: bool = True,
        enable_cost_optimizer: bool = True,
        enable_backup_manager: bool = True,
        use_mock: bool = False
    ):
        """
        Initialize the prediction service.
        
        Args:
            metrics_interval: Seconds between metrics collection
            prediction_interval: Seconds between predictions
            auto_remediate: Whether to automatically apply remediation
            kubeconfig_path: Optional path to kubeconfig file
            history_file: Optional path to store prediction history
            remediation_history_file: Optional path to store remediation history
            security_scan_interval: Seconds between security scans
            cost_analysis_interval: Seconds between cost analyses
            enable_security_scanner: Whether to enable security scanning
            enable_cost_optimizer: Whether to enable cost optimization
            enable_backup_manager: Whether to enable backup manager
            use_mock: Use mock data instead of real Kubernetes cluster
        """
        self.metrics_interval = metrics_interval
        self.prediction_interval = prediction_interval
        self.auto_remediate = auto_remediate
        self.history_file = history_file
        self.remediation_history_file = remediation_history_file
        self.use_mock = use_mock
        
        # Initialize components
        self.metrics_collector = KubernetesMetricsCollector(
            kubeconfig_path=kubeconfig_path,
            metrics_history_file=history_file,
            use_mock=use_mock
        )
        self.predictor = KubernetesPredictor(
            model_path=None,  # TODO: Add model path configuration
            history_file=history_file
        )
        self.remediator = KubernetesRemediator(
            auto_remediate=auto_remediate,
            kubeconfig_path=kubeconfig_path,
            remediation_history_file=remediation_history_file,
            use_mock=use_mock
        )
        
        # Initialize new components
        if enable_security_scanner:
            self.security_scanner = KubernetesSecurityScanner(
                kubeconfig_path=kubeconfig_path,
                scan_interval=security_scan_interval,
                history_file=self._get_history_path("security_history.json"),
                use_mock=use_mock
            )
        else:
            self.security_scanner = None
            
        if enable_cost_optimizer:
            self.cost_optimizer = KubernetesCostOptimizer(
                kubeconfig_path=kubeconfig_path,
                analyze_interval=cost_analysis_interval,
                history_file=self._get_history_path("cost_history.json"),
                use_mock=use_mock
            )
        else:
            self.cost_optimizer = None
            
        if enable_backup_manager:
            self.backup_manager = KubernetesBackupManager(
                kubeconfig_path=kubeconfig_path,
                history_file=self._get_history_path("backup_history.json"),
                use_mock=use_mock
            )
        else:
            self.backup_manager = None
        
        # State
        self._running = False
        self._prediction_thread = None
        self._last_prediction = None
        self._last_remediation = None
        self._prediction_history = []
        self.max_history_size = 1000
        
        logger.info(
            "Initialized KubernetesPredictionService with metrics_interval=%d, "
            "prediction_interval=%d, auto_remediate=%s",
            metrics_interval, prediction_interval, auto_remediate
        )
    
    def _get_history_path(self, filename: str) -> str:
        """Helper to generate history file paths."""
        if not self.history_file:
            return None
            
        # Get directory from history_file
        history_dir = os.path.dirname(self.history_file)
        if not history_dir:
            history_dir = os.path.expanduser("~/.kagent")
            
        return os.path.join(history_dir, filename)
    
    def start(self):
        """Start the prediction service."""
        if self._running:
            logger.warning("Service is already running")
            return
        
        self._running = True
        self.metrics_collector.start()
        
        # Start prediction loop in a separate thread
        self._prediction_thread = threading.Thread(
            target=self._prediction_loop,
            daemon=True
        )
        self._prediction_thread.start()
        
        # Start security scanning if enabled
        if self.security_scanner:
            self.security_scanner.start_scanning_loop()
            
        # Start cost optimization if enabled
        if self.cost_optimizer:
            self.cost_optimizer.start_analysis_loop()
        
        logger.info("Started KubernetesPredictionService")
    
    def stop(self):
        """Stop the prediction service."""
        if not self._running:
            logger.warning("Service is not running")
            return
        
        self._running = False
        self.metrics_collector.stop()
        
        if self._prediction_thread:
            self._prediction_thread.join(timeout=5)
            self._prediction_thread = None
            
        # Stop security scanning if enabled
        if self.security_scanner:
            self.security_scanner.stop_scanning_loop()
            
        # Stop cost optimization if enabled
        if self.cost_optimizer:
            self.cost_optimizer.stop_analysis_loop()
        
        logger.info("Stopped KubernetesPredictionService")
    
    def _prediction_loop(self):
        """Main prediction loop that runs in a separate thread."""
        while self._running:
            try:
                # Get latest metrics
                metrics = self.metrics_collector.get_formatted_metrics()
                if not metrics:
                    logger.warning("No metrics available for prediction")
                    time.sleep(self.prediction_interval)
                    continue
                
                # Make prediction
                prediction = self.predictor.analyze_metrics(metrics)
                self._last_prediction = prediction
                
                # Record prediction
                self._record_prediction(prediction)
                
                # Handle remediation if needed
                if prediction.issues:
                    self._handle_remediation(prediction)
                
                # Wait for next prediction interval
                time.sleep(self.prediction_interval)
            
            except Exception as e:
                logger.error(f"Error in prediction loop: {e}")
                time.sleep(self.prediction_interval)
    
    def _handle_remediation(self, prediction):
        """
        Handle remediation for predicted issues.
        
        Args:
            prediction: PredictionResult containing identified issues
        """
        for issue in prediction.issues:
            try:
                # Attempt remediation
                result = self.remediator.remediate_issue(issue)
                self._last_remediation = result
                
                # Log result
                if result.success:
                    logger.info(
                        "Successfully remediated issue: %s on %s",
                        issue.get("type", "unknown"), issue.get("component", "unknown")
                    )
                else:
                    logger.warning(
                        "Failed to remediate issue: %s on %s: %s",
                        issue.get("type", "unknown"), issue.get("component", "unknown"), result.error_message
                    )
            
            except Exception as e:
                logger.error(f"Error during remediation: {e}")
    
    def _record_prediction(self, prediction):
        """Record a prediction in history."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "prediction": prediction.dict()
        }
        
        self._prediction_history.append(record)
        if len(self._prediction_history) > self.max_history_size:
            self._prediction_history.pop(0)
        
        # Save history if configured
        if self.history_file:
            self._save_prediction_history()
    
    def _save_prediction_history(self):
        """Save prediction history to file."""
        if not self.history_file:
            return
        
        try:
            history_file = Path(self.history_file)
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(history_file, "w") as f:
                json.dump(self._prediction_history, f, indent=2)
            
            logger.debug(f"Saved prediction history to {self.history_file}")
        except Exception as e:
            logger.error(f"Error saving prediction history: {e}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get the current status of the prediction service.
        
        Returns:
            Dictionary containing current status information
        """
        return {
            "running": self._running,
            "last_prediction": self._last_prediction.dict() if self._last_prediction else None,
            "last_remediation": self._last_remediation.dict() if self._last_remediation else None,
            "metrics_collector": {
                "running": self.metrics_collector.is_running(),
                "last_collection": self.metrics_collector.get_last_collection_time()
            }
        }
    
    def get_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get trends from prediction history.
        
        Args:
            hours: Number of hours of history to analyze
            
        Returns:
            Dictionary containing trend analysis
        """
        if not self._prediction_history:
            return {}
        
        # Filter history to requested time range
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_history = [
            record for record in self._prediction_history
            if datetime.fromisoformat(record["timestamp"]) > cutoff
        ]
        
        # Analyze trends
        issue_counts = {}
        remediation_counts = {}
        
        for record in recent_history:
            prediction = record["prediction"]
            
            # Count issues by type
            for issue in prediction["issues"]:
                issue_type = issue.get("type", "unknown")
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
            
            # Count remediations
            if prediction.get("remediation_applied"):
                remediation_type = prediction["remediation_applied"].get("type", "unknown")
                remediation_counts[remediation_type] = remediation_counts.get(remediation_type, 0) + 1
        
        return {
            "issue_trends": issue_counts,
            "remediation_trends": remediation_counts,
            "total_predictions": len(recent_history)
        }
    
    def get_security_scan_results(self) -> Optional[Dict[str, Any]]:
        """Get latest security scan results."""
        if not self.security_scanner:
            return {"error": "Security scanner not enabled"}
            
        latest_scan = self.security_scanner.get_latest_scan_results()
        if not latest_scan:
            return {"error": "No security scans have been performed"}
            
        return latest_scan
        
    def run_security_scan(self) -> Dict[str, Any]:
        """Run a security scan and return results."""
        if not self.security_scanner:
            return {"error": "Security scanner not enabled"}
            
        try:
            scan_result = self.security_scanner.perform_security_scan()
            return scan_result.to_dict()
        except Exception as e:
            logger.error(f"Error performing security scan: {e}")
            return {"error": str(e)}
    
    def get_cost_optimization_suggestions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get cost optimization suggestions."""
        if not self.cost_optimizer:
            return {"error": "Cost optimizer not enabled"}
            
        return self.cost_optimizer.get_optimization_suggestions(limit)
        
    def get_estimated_savings(self) -> Dict[str, float]:
        """Get estimated cost savings."""
        if not self.cost_optimizer:
            return {"error": "Cost optimizer not enabled"}
            
        return self.cost_optimizer.get_estimated_total_savings()
    
    def run_cost_analysis(self) -> List[Dict[str, Any]]:
        """Run cost analysis and return suggestions."""
        if not self.cost_optimizer:
            return {"error": "Cost optimizer not enabled"}
            
        try:
            # Ensure we have fresh metrics
            self.cost_optimizer._collect_current_metrics()
            
            # Run analysis
            suggestions = self.cost_optimizer.analyze_cost_optimization()
            return [s.to_dict() for s in suggestions]
        except Exception as e:
            logger.error(f"Error performing cost analysis: {e}")
            return {"error": str(e)}
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get list of backups."""
        if not self.backup_manager:
            return {"error": "Backup manager not enabled"}
            
        return self.backup_manager.get_backup_list()
    
    def get_restore_list(self) -> List[Dict[str, Any]]:
        """Get list of restore operations."""
        if not self.backup_manager:
            return {"error": "Backup manager not enabled"}
            
        return self.backup_manager.get_restore_list()
    
    def run_manual_prediction(self) -> Dict[str, Any]:
        """
        Run a manual prediction and return results immediately.
        
        Returns:
            Dictionary containing prediction results and remediation suggestions
        """
        try:
            # Get latest metrics
            metrics = self.metrics_collector.get_formatted_metrics()
            if not metrics:
                return {"error": "No metrics available for prediction"}
            
            # Make prediction
            prediction = self.predictor.analyze_metrics(metrics)
            self._last_prediction = prediction
            
            # Generate remediation suggestions
            remediation_suggestions = []
            for issue in prediction.issues:
                suggestions = self.remediator.get_remediation_suggestions(issue)
                if suggestions:
                    remediation_suggestions.append({
                        "issue_type": issue.get("type", "unknown"),
                        "component": issue.get("component", "unknown"),
                        "actions": suggestions
                    })
            
            # Format result
            result = {
                "timestamp": datetime.now().isoformat(),
                "issues": prediction.issues,  # Issues are already dictionaries
                "remediation_suggestions": remediation_suggestions
            }
            
            return result
        except Exception as e:
            logger.error(f"Error running manual prediction: {e}")
            return {"error": str(e)} 