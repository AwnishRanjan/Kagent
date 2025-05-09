"""
Kubernetes Cost Optimization Agent

This module provides cost optimization capabilities for Kubernetes clusters,
analyzing resource allocation and usage patterns to suggest cost-saving measures.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading
import time
import json
from pathlib import Path
import statistics

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class OptimizationSuggestion:
    """Model representing a cost optimization suggestion"""
    def __init__(self, 
                resource_type: str,
                namespace: str,
                name: str,
                current_allocation: Dict[str, Any],
                suggested_allocation: Dict[str, Any],
                estimated_savings: Dict[str, float],
                confidence: float,
                priority: str):
        self.resource_type = resource_type
        self.namespace = namespace
        self.name = name
        self.current_allocation = current_allocation
        self.suggested_allocation = suggested_allocation
        self.estimated_savings = estimated_savings
        self.confidence = confidence  # 0.0 to 1.0
        self.priority = priority  # "high", "medium", "low"
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_type": self.resource_type,
            "namespace": self.namespace,
            "name": self.name,
            "current_allocation": self.current_allocation,
            "suggested_allocation": self.suggested_allocation,
            "estimated_savings": self.estimated_savings,
            "confidence": self.confidence,
            "priority": self.priority,
            "timestamp": self.timestamp
        }

class KubernetesCostOptimizer:
    """
    Provides cost optimization capabilities for Kubernetes clusters.
    
    This optimizer:
    - Identifies over-provisioned resources
    - Suggests right-sizing for pods and nodes
    - Identifies idle or underutilized resources
    - Recommends appropriate instance types
    - Calculates potential cost savings
    """
    
    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        analyze_interval: int = 86400,  # Default: analyze daily
        metrics_window: int = 7,  # Days of metrics to analyze
        history_file: Optional[str] = None,
        cloud_provider: str = "aws",  # "aws", "gcp", "azure"
        pricing_data: Optional[Dict[str, Any]] = None,
        use_mock: bool = False
    ):
        """
        Initialize the cost optimizer.
        
        Args:
            kubeconfig_path: Optional path to kubeconfig file
            analyze_interval: How often to perform analysis, in seconds
            metrics_window: Days of metrics history to analyze
            history_file: Optional path to store optimization history
            cloud_provider: Cloud provider for pricing calculations
            pricing_data: Optional pricing data for cost calculations
            use_mock: Whether to use mock data instead of connecting to a real Kubernetes cluster
        """
        self.analyze_interval = analyze_interval
        self.metrics_window = metrics_window
        self.history_file = history_file
        self.optimization_history = []
        self.max_history_size = 100
        self.cloud_provider = cloud_provider
        self.pricing_data = pricing_data or self._get_default_pricing_data()
        self.use_mock = use_mock
        
        if not self.use_mock:
            # Initialize Kubernetes client only if not in mock mode
            try:
                if kubeconfig_path:
                    config.load_kube_config(config_file=kubeconfig_path)
                else:
                    # Try loading from default location
                    try:
                        config.load_kube_config()
                    except Exception:
                        # Fall back to in-cluster config for running inside a pod
                        config.load_incluster_config()
                
                self.core_v1 = client.CoreV1Api()
                self.apps_v1 = client.AppsV1Api()
                self.metrics_api = client.CustomObjectsApi()
                logger.info("Successfully initialized Kubernetes client for cost optimization")
            except Exception as e:
                logger.error(f"Failed to initialize Kubernetes client: {e}")
                raise
        else:
            # In mock mode, set API clients to None
            logger.info("Initializing cost optimizer in mock mode")
            self.core_v1 = None
            self.apps_v1 = None
            self.metrics_api = None
        
        # Analysis state
        self.running = False
        self.analysis_thread = None
        
        # Storage for metrics history
        self.metrics_history = {}  # {resource_id: [metrics]}
    
    def _get_default_pricing_data(self) -> Dict[str, Any]:
        """
        Get default pricing data for cost calculations.
        This is a simplified version - in production, you'd use real pricing APIs.
        """
        return {
            "cpu_cost_per_core_hour": {
                "aws": 0.0425,
                "gcp": 0.0440,
                "azure": 0.0450
            },
            "memory_cost_per_gb_hour": {
                "aws": 0.0050,
                "gcp": 0.0055,
                "azure": 0.0060
            },
            "storage_cost_per_gb_month": {
                "aws": 0.10,
                "gcp": 0.12,
                "azure": 0.11
            },
            "instance_types": {
                "aws": {
                    "t3.small": {"cpu": 2, "memory": 2, "cost_per_hour": 0.0209},
                    "t3.medium": {"cpu": 2, "memory": 4, "cost_per_hour": 0.0418},
                    "t3.large": {"cpu": 2, "memory": 8, "cost_per_hour": 0.0835},
                    "m5.large": {"cpu": 2, "memory": 8, "cost_per_hour": 0.0960},
                    "m5.xlarge": {"cpu": 4, "memory": 16, "cost_per_hour": 0.1920},
                    "m5.2xlarge": {"cpu": 8, "memory": 32, "cost_per_hour": 0.3840},
                    "c5.large": {"cpu": 2, "memory": 4, "cost_per_hour": 0.0850},
                    "c5.xlarge": {"cpu": 4, "memory": 8, "cost_per_hour": 0.1700},
                    "r5.large": {"cpu": 2, "memory": 16, "cost_per_hour": 0.1260},
                    "r5.xlarge": {"cpu": 4, "memory": 32, "cost_per_hour": 0.2520}
                }
            }
        }
    
    def start_analysis_loop(self):
        """Start the background cost analysis loop."""
        if self.running:
            logger.warning("Cost analysis loop is already running")
            return
        
        self.running = True
        self.analysis_thread = threading.Thread(target=self._analysis_loop)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        logger.info("Started cost optimization analysis loop")
    
    def stop_analysis_loop(self):
        """Stop the background cost analysis loop."""
        if not self.running:
            logger.warning("Cost analysis loop is not running")
            return
        
        self.running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5.0)
        
        # Save optimization history if configured
        if self.history_file:
            self._save_optimization_history()
        
        logger.info("Stopped cost optimization analysis loop")
    
    def _analysis_loop(self):
        """Background loop for performing cost analysis at regular intervals."""
        while self.running:
            try:
                # Collect metrics for current state
                self._collect_current_metrics()
                
                # Perform optimization analysis
                suggestions = self.analyze_cost_optimization()
                
                # Save suggestions
                for suggestion in suggestions:
                    self.optimization_history.append(suggestion.to_dict())
                
                # Trim history if needed
                if len(self.optimization_history) > self.max_history_size:
                    self.optimization_history = self.optimization_history[-self.max_history_size:]
                
                # Save history
                if self.history_file:
                    self._save_optimization_history()
                
                logger.info(f"Completed cost optimization analysis, found {len(suggestions)} optimization opportunities")
            except Exception as e:
                logger.error(f"Error performing cost optimization analysis: {e}")
            
            time.sleep(self.analyze_interval)
    
    def _collect_current_metrics(self):
        """Collect current metrics for resource usage analysis."""
        if self.use_mock:
            # Generate mock metrics in mock mode
            self._generate_mock_metrics()
            return
        
        try:
            # Get pod metrics
            pod_metrics = self._get_pod_metrics()
            
            # Get node metrics
            node_metrics = self._get_node_metrics()
            
            # Store in metrics history
            timestamp = datetime.now().isoformat()
            
            for pod_id, pod_data in pod_metrics.items():
                if pod_id not in self.metrics_history:
                    self.metrics_history[pod_id] = []
                
                self.metrics_history[pod_id].append({
                    "timestamp": timestamp,
                    "cpu_usage": pod_data.get("cpu_usage", 0),
                    "memory_usage": pod_data.get("memory_usage", 0),
                    "cpu_request": pod_data.get("cpu_request", 0),
                    "memory_request": pod_data.get("memory_request", 0),
                    "cpu_limit": pod_data.get("cpu_limit", 0),
                    "memory_limit": pod_data.get("memory_limit", 0)
                })
            
            for node_id, node_data in node_metrics.items():
                if node_id not in self.metrics_history:
                    self.metrics_history[node_id] = []
                
                self.metrics_history[node_id].append({
                    "timestamp": timestamp,
                    "cpu_usage": node_data.get("cpu_usage", 0),
                    "memory_usage": node_data.get("memory_usage", 0),
                    "cpu_capacity": node_data.get("cpu_capacity", 0),
                    "memory_capacity": node_data.get("memory_capacity", 0),
                    "pods_running": node_data.get("pods_running", 0)
                })
            
            # Trim history to only keep metrics_window days
            cutoff = datetime.now() - timedelta(days=self.metrics_window)
            cutoff_str = cutoff.isoformat()
            
            for resource_id in self.metrics_history:
                self.metrics_history[resource_id] = [
                    m for m in self.metrics_history[resource_id]
                    if m["timestamp"] >= cutoff_str
                ]
            
            logger.debug("Collected metrics for cost optimization analysis")
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    def _get_pod_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get current metrics for all pods."""
        # In mock mode, return an empty dict as metrics will be generated by _generate_mock_metrics
        if self.use_mock:
            return {}
            
        pod_metrics = {}
        
        try:
            # Get pod metrics from metrics-server
            metrics_data = self.metrics_api.list_cluster_custom_object(
                "metrics.k8s.io", "v1beta1", "pods"
            )
            
            for pod_metric in metrics_data.get("items", []):
                namespace = pod_metric["metadata"]["namespace"]
                name = pod_metric["metadata"]["name"]
                pod_id = f"{namespace}/{name}"
                
                # Get CPU and memory usage
                containers = pod_metric.get("containers", [])
                cpu_usage = sum(self._parse_cpu_value(c.get("usage", {}).get("cpu", "0")) for c in containers)
                memory_usage = sum(self._parse_memory_value(c.get("usage", {}).get("memory", "0")) for c in containers)
                
                # Get pod details including resource requests and limits
                try:
                    pod = self.core_v1.read_namespaced_pod(name, namespace)
                    
                    # Calculate total requests and limits
                    cpu_request = 0
                    cpu_limit = 0
                    memory_request = 0
                    memory_limit = 0
                    
                    for container in pod.spec.containers:
                        if container.resources:
                            if container.resources.requests:
                                cpu_request += self._parse_cpu_value(container.resources.requests.get("cpu", "0"))
                                memory_request += self._parse_memory_value(container.resources.requests.get("memory", "0"))
                            
                            if container.resources.limits:
                                cpu_limit += self._parse_cpu_value(container.resources.limits.get("cpu", "0"))
                                memory_limit += self._parse_memory_value(container.resources.limits.get("memory", "0"))
                    
                    # Calculate utilization percentages
                    cpu_request_utilization = (cpu_usage / cpu_request * 100) if cpu_request > 0 else 0
                    memory_request_utilization = (memory_usage / memory_request * 100) if memory_request > 0 else 0
                    
                    pod_metrics[pod_id] = {
                        "cpu_usage": cpu_usage,  # cores
                        "memory_usage": memory_usage,  # bytes
                        "cpu_request": cpu_request,  # cores
                        "memory_request": memory_request,  # bytes
                        "cpu_limit": cpu_limit,  # cores
                        "memory_limit": memory_limit,  # bytes
                        "cpu_request_utilization": cpu_request_utilization,  # percentage
                        "memory_request_utilization": memory_request_utilization,  # percentage
                        "restarts": sum(c.restart_count for c in pod.status.container_statuses) if pod.status.container_statuses else 0,
                        "node": pod.spec.node_name
                    }
                
                except ApiException:
                    # Pod might have been deleted since metrics were collected
                    continue
        
        except ApiException as e:
            logger.error(f"Error getting pod metrics: {e}")
        
        return pod_metrics
    
    def _get_node_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get current metrics for all nodes."""
        # In mock mode, return an empty dict as metrics will be generated by _generate_mock_metrics
        if self.use_mock:
            return {}
            
        node_metrics = {}
        
        try:
            # Get all nodes
            nodes = self.core_v1.list_node()
            
            # Get node metrics from metrics-server
            metrics_data = self.metrics_api.list_cluster_custom_object(
                "metrics.k8s.io", "v1beta1", "nodes"
            )
            
            # Build node metrics lookup
            node_metrics_lookup = {}
            for node_metric in metrics_data.get("items", []):
                name = node_metric["metadata"]["name"]
                node_metrics_lookup[name] = {
                    "cpu_usage": self._parse_cpu_value(node_metric.get("usage", {}).get("cpu", "0")),
                    "memory_usage": self._parse_memory_value(node_metric.get("usage", {}).get("memory", "0"))
                }
            
            # Process each node
            for node in nodes.items:
                name = node.metadata.name
                
                # Get allocatable resources
                allocatable = node.status.allocatable
                cpu_capacity = self._parse_cpu_value(allocatable.get("cpu", "0"))
                memory_capacity = self._parse_memory_value(allocatable.get("memory", "0"))
                
                # Get current usage from metrics
                metrics = node_metrics_lookup.get(name, {})
                cpu_usage = metrics.get("cpu_usage", 0)
                memory_usage = metrics.get("memory_usage", 0)
                
                # Calculate utilization percentages
                cpu_utilization = (cpu_usage / cpu_capacity * 100) if cpu_capacity > 0 else 0
                memory_utilization = (memory_usage / memory_capacity * 100) if memory_capacity > 0 else 0
                
                # Get node labels for identifying instance type
                labels = node.metadata.labels or {}
                instance_type = labels.get("node.kubernetes.io/instance-type", 
                                          labels.get("beta.kubernetes.io/instance-type", "unknown"))
                
                node_metrics[name] = {
                    "cpu_capacity": cpu_capacity,  # cores
                    "memory_capacity": memory_capacity,  # bytes
                    "cpu_usage": cpu_usage,  # cores
                    "memory_usage": memory_usage,  # bytes
                    "cpu_utilization": cpu_utilization,  # percentage
                    "memory_utilization": memory_utilization,  # percentage
                    "instance_type": instance_type,
                    "labels": labels
                }
        
        except ApiException as e:
            logger.error(f"Error getting node metrics: {e}")
        
        return node_metrics
    
    def analyze_cost_optimization(self) -> List[OptimizationSuggestion]:
        """
        Analyze resource usage and suggest cost optimization opportunities.
        
        Returns:
            List of cost optimization suggestions
        """
        if not self.metrics_history and not self.use_mock:
            # Collect metrics if we don't have any and not in mock mode
            self._collect_current_metrics()
        elif self.use_mock and not self.metrics_history:
            # Generate mock metrics in mock mode
            self._generate_mock_metrics()
        
        # Analyze different optimization opportunities
        pod_suggestions = self._analyze_pod_optimization()
        node_suggestions = self._analyze_node_optimization()
        quota_suggestions = self._analyze_quota_optimization()
        
        # Combine all suggestions
        all_suggestions = pod_suggestions + node_suggestions + quota_suggestions
        
        # Sort by estimated savings (highest first)
        all_suggestions.sort(
            key=lambda s: s.estimated_savings.get("total_monthly", 0), 
            reverse=True
        )
        
        return all_suggestions
    
    def _analyze_pod_optimization(self) -> List[OptimizationSuggestion]:
        """Analyze pods for resource optimization opportunities."""
        suggestions = []
        
        for pod_id, history in self.metrics_history.items():
            if not history or "/" not in pod_id:
                continue
            
            namespace, name = pod_id.split("/", 1)
            
            try:
                # Get current pod
                try:
                    pod = self.core_v1.read_namespaced_pod(name, namespace)
                except ApiException:
                    # Pod no longer exists
                    continue
                
                # Skip pods that are not Running
                if pod.status.phase != "Running":
                    continue
                
                # Check if it's part of a workload controller
                owner_references = pod.metadata.owner_references or []
                if not owner_references:
                    # Skip standalone pods
                    continue
                
                # Only analyze pods controlled by Deployments, StatefulSets, etc.
                controller_kind = owner_references[0].kind
                if controller_kind not in ["Deployment", "StatefulSet", "ReplicaSet", "DaemonSet"]:
                    continue
                
                # Get metrics history
                cpu_usages = []
                memory_usages = []
                cpu_requests = []
                memory_requests = []
                
                for entry in history:
                    metrics = entry.get("metrics", {})
                    cpu_usages.append(metrics.get("cpu_usage", 0))
                    memory_usages.append(metrics.get("memory_usage", 0))
                    cpu_requests.append(metrics.get("cpu_request", 0))
                    memory_requests.append(metrics.get("memory_request", 0))
                
                if not cpu_usages or not memory_usages:
                    continue
                
                # Calculate statistics
                avg_cpu_usage = statistics.mean(cpu_usages)
                max_cpu_usage = max(cpu_usages)
                p95_cpu_usage = sorted(cpu_usages)[int(len(cpu_usages) * 0.95)]
                
                avg_memory_usage = statistics.mean(memory_usages)
                max_memory_usage = max(memory_usages)
                p95_memory_usage = sorted(memory_usages)[int(len(memory_usages) * 0.95)]
                
                # Get current requests/limits for calculation
                current_cpu_request = cpu_requests[-1] if cpu_requests else 0
                current_memory_request = memory_requests[-1] if memory_requests else 0
                
                # Check for over-provisioning
                if current_cpu_request > 0 and current_memory_request > 0:
                    cpu_overprovisioned = p95_cpu_usage / current_cpu_request < 0.5
                    memory_overprovisioned = p95_memory_usage / current_memory_request < 0.5
                    
                    if cpu_overprovisioned or memory_overprovisioned:
                        # Calculate recommended values (using p95 with a 20% buffer)
                        recommended_cpu = max(0.1, p95_cpu_usage * 1.2)  # Minimum 0.1 core
                        recommended_memory = max(128 * 1024 * 1024, p95_memory_usage * 1.2)  # Minimum 128Mi
                        
                        # Format memory for display
                        if recommended_memory < 1024 * 1024 * 1024:
                            recommended_memory_str = f"{int(recommended_memory / 1024 / 1024)}Mi"
                        else:
                            recommended_memory_str = f"{round(recommended_memory / 1024 / 1024 / 1024, 1)}Gi"
                        
                        # Calculate potential savings
                        cpu_saved = current_cpu_request - recommended_cpu
                        memory_saved = current_memory_request - recommended_memory
                        
                        # Calculate cost savings if positive
                        cpu_cost_per_hour = self.pricing_data["cpu_cost_per_core_hour"][self.cloud_provider]
                        memory_cost_per_gb_hour = self.pricing_data["memory_cost_per_gb_hour"][self.cloud_provider]
                        
                        cpu_savings = max(0, cpu_saved * cpu_cost_per_hour * 24 * 30)  # Monthly
                        memory_savings = max(0, (memory_saved / 1024 / 1024 / 1024) * memory_cost_per_gb_hour * 24 * 30)  # Monthly
                        total_savings = cpu_savings + memory_savings
                        
                        # Only suggest changes with meaningful savings
                        if total_savings > 1.0:  # $1 per month minimum threshold
                            # Determine confidence based on history length
                            confidence = min(0.9, len(history) / (self.metrics_window * 24 * 0.5))  # 0.5 = 12 hours of data per day
                            
                            # Determine priority based on savings
                            priority = "low"
                            if total_savings > 50:
                                priority = "high"
                            elif total_savings > 10:
                                priority = "medium"
                            
                            suggestion = OptimizationSuggestion(
                                resource_type=controller_kind,
                                namespace=namespace,
                                name=owner_references[0].name,
                                current_allocation={
                                    "cpu_request": f"{current_cpu_request}",
                                    "memory_request": f"{int(current_memory_request / 1024 / 1024)}Mi"
                                },
                                suggested_allocation={
                                    "cpu_request": f"{round(recommended_cpu, 2)}",
                                    "memory_request": recommended_memory_str
                                },
                                estimated_savings={
                                    "cpu_monthly": round(cpu_savings, 2),
                                    "memory_monthly": round(memory_savings, 2),
                                    "total_monthly": round(total_savings, 2)
                                },
                                confidence=confidence,
                                priority=priority
                            )
                            
                            suggestions.append(suggestion)
            
            except Exception as e:
                logger.error(f"Error analyzing pod {pod_id} for optimization: {e}")
        
        return suggestions
    
    def _analyze_node_optimization(self) -> List[OptimizationSuggestion]:
        """Analyze nodes for resource optimization opportunities."""
        suggestions = []
        
        # Get all nodes' metrics history
        node_histories = {k: v for k, v in self.metrics_history.items() if "/" not in k}
        
        # Group nodes by instance type
        instance_type_nodes = {}
        
        for node_name, history in node_histories.items():
            if not history:
                continue
            
            latest_metrics = history[-1].get("metrics", {})
            instance_type = latest_metrics.get("instance_type", "unknown")
            
            if instance_type not in instance_type_nodes:
                instance_type_nodes[instance_type] = []
            
            instance_type_nodes[instance_type].append((node_name, history))
        
        # Analyze each instance type group
        for instance_type, nodes in instance_type_nodes.items():
            if instance_type == "unknown" or len(nodes) < 2:
                continue
            
            # Calculate average utilization across all nodes of this type
            avg_cpu_utilization = []
            avg_memory_utilization = []
            
            for _, history in nodes:
                cpu_utils = [entry.get("metrics", {}).get("cpu_utilization", 0) for entry in history]
                memory_utils = [entry.get("metrics", {}).get("memory_utilization", 0) for entry in history]
                
                if cpu_utils and memory_utils:
                    avg_cpu_utilization.append(statistics.mean(cpu_utils))
                    avg_memory_utilization.append(statistics.mean(memory_utils))
            
            if not avg_cpu_utilization or not avg_memory_utilization:
                continue
            
            # Calculate overall averages
            overall_cpu_avg = statistics.mean(avg_cpu_utilization)
            overall_memory_avg = statistics.mean(avg_memory_utilization)
            
            # Check if the nodes are consistently underutilized
            if overall_cpu_avg < 40 and overall_memory_avg < 50 and len(nodes) > 1:
                # We could potentially reduce the node count
                current_node_count = len(nodes)
                suggested_node_count = max(1, int(current_node_count * 0.8))  # Reduce by 20% with minimum of 1
                
                if suggested_node_count < current_node_count:
                    # Calculate savings
                    hourly_cost_per_instance = 0.0
                    if instance_type in self.pricing_data["instance_types"].get(self.cloud_provider, {}):
                        hourly_cost_per_instance = self.pricing_data["instance_types"][self.cloud_provider][instance_type]["cost_per_hour"]
                    
                    nodes_saved = current_node_count - suggested_node_count
                    monthly_savings = nodes_saved * hourly_cost_per_instance * 24 * 30
                    
                    # Only suggest meaningful savings
                    if monthly_savings > 10:  # $10 per month minimum threshold
                        suggestion = OptimizationSuggestion(
                            resource_type="NodeGroup",
                            namespace="",
                            name=instance_type,
                            current_allocation={
                                "node_count": current_node_count,
                                "avg_cpu_utilization": f"{round(overall_cpu_avg, 1)}%",
                                "avg_memory_utilization": f"{round(overall_memory_avg, 1)}%"
                            },
                            suggested_allocation={
                                "node_count": suggested_node_count,
                                "estimated_cpu_utilization": f"{round(overall_cpu_avg * current_node_count / suggested_node_count, 1)}%",
                                "estimated_memory_utilization": f"{round(overall_memory_avg * current_node_count / suggested_node_count, 1)}%"
                            },
                            estimated_savings={
                                "nodes_reduced": nodes_saved,
                                "total_monthly": round(monthly_savings, 2)
                            },
                            confidence=0.7,  # Fixed confidence since this is a higher risk change
                            priority="high" if monthly_savings > 100 else "medium"
                        )
                        
                        suggestions.append(suggestion)
        
        return suggestions
    
    def _analyze_quota_optimization(self) -> List[OptimizationSuggestion]:
        """Analyze namespace resource quotas for optimization opportunities."""
        suggestions = []
        
        try:
            # Get all namespaces
            namespaces = self.core_v1.list_namespace()
            
            for namespace in namespaces.items:
                ns_name = namespace.metadata.name
                
                # Skip system namespaces
                if ns_name in ["kube-system", "kube-public", "kube-node-lease"]:
                    continue
                
                try:
                    # Get current resource quota if it exists
                    quotas = self.core_v1.list_namespaced_resource_quota(ns_name)
                    
                    if not quotas.items:
                        # Check namespace resource usage
                        pod_cpu_usage = 0
                        pod_memory_usage = 0
                        pod_cpu_requests = 0
                        pod_memory_requests = 0
                        
                        # Get all pods in this namespace
                        pods = self.core_v1.list_namespaced_pod(ns_name)
                        
                        for pod in pods.items:
                            # Skip non-running pods
                            if pod.status.phase != "Running":
                                continue
                            
                            # Get pod metrics
                            pod_name = pod.metadata.name
                            pod_id = f"{ns_name}/{pod_name}"
                            
                            if pod_id in self.metrics_history and self.metrics_history[pod_id]:
                                latest_metrics = self.metrics_history[pod_id][-1].get("metrics", {})
                                pod_cpu_usage += latest_metrics.get("cpu_usage", 0)
                                pod_memory_usage += latest_metrics.get("memory_usage", 0)
                                pod_cpu_requests += latest_metrics.get("cpu_request", 0)
                                pod_memory_requests += latest_metrics.get("memory_request", 0)
                        
                        # If significant resources are being used, suggest a quota
                        if pod_cpu_requests > 4 or pod_memory_requests > 4 * 1024 * 1024 * 1024:  # 4 cores or 4GB
                            # Suggest quota with 20% headroom
                            suggested_cpu_quota = max(1, int(pod_cpu_requests * 1.2))
                            suggested_memory_quota = max(1024 * 1024 * 1024, int(pod_memory_requests * 1.2))
                            
                            suggestion = OptimizationSuggestion(
                                resource_type="ResourceQuota",
                                namespace=ns_name,
                                name=f"{ns_name}-quota",
                                current_allocation={
                                    "cpu_requests": f"{pod_cpu_requests}",
                                    "memory_requests": f"{int(pod_memory_requests / 1024 / 1024 / 1024)}Gi",
                                    "quota": "None"
                                },
                                suggested_allocation={
                                    "cpu_requests": f"{suggested_cpu_quota}",
                                    "memory_requests": f"{int(suggested_memory_quota / 1024 / 1024 / 1024)}Gi",
                                    "action": "Create ResourceQuota"
                                },
                                estimated_savings={
                                    "monthly": 0,  # No direct savings, but helps prevent resource sprawl
                                    "risk_mitigation": "high"
                                },
                                confidence=0.8,
                                priority="medium"
                            )
                            
                            suggestions.append(suggestion)
                
                except ApiException:
                    continue
        
        except ApiException as e:
            logger.error(f"Error analyzing resource quotas: {e}")
        
        return suggestions
    
    def _parse_cpu_value(self, cpu_str: str) -> float:
        """Parse CPU string value to cores as float."""
        if not cpu_str:
            return 0.0
        
        try:
            if cpu_str.endswith("m"):
                return float(cpu_str[:-1]) / 1000.0
            elif cpu_str.endswith("n"):
                return float(cpu_str[:-1]) / 1000000000.0
            else:
                return float(cpu_str)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_memory_value(self, memory_str: str) -> int:
        """Parse memory string value to bytes as int."""
        if not memory_str:
            return 0
        
        try:
            if memory_str.endswith("Ki"):
                return int(float(memory_str[:-2]) * 1024)
            elif memory_str.endswith("Mi"):
                return int(float(memory_str[:-2]) * 1024 * 1024)
            elif memory_str.endswith("Gi"):
                return int(float(memory_str[:-2]) * 1024 * 1024 * 1024)
            elif memory_str.endswith("Ti"):
                return int(float(memory_str[:-2]) * 1024 * 1024 * 1024 * 1024)
            elif memory_str.endswith("K") or memory_str.endswith("k"):
                return int(float(memory_str[:-1]) * 1000)
            elif memory_str.endswith("M"):
                return int(float(memory_str[:-1]) * 1000 * 1000)
            elif memory_str.endswith("G"):
                return int(float(memory_str[:-1]) * 1000 * 1000 * 1000)
            elif memory_str.endswith("T"):
                return int(float(memory_str[:-1]) * 1000 * 1000 * 1000 * 1000)
            else:
                return int(memory_str)
        except (ValueError, TypeError):
            return 0
    
    def _save_optimization_history(self):
        """Save optimization history to file."""
        if not self.history_file:
            return
        
        try:
            history_path = Path(self.history_file)
            history_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(history_path, 'w') as f:
                json.dump(self.optimization_history, f, indent=2)
            
            logger.debug(f"Saved optimization history to {self.history_file}")
        except Exception as e:
            logger.error(f"Error saving optimization history: {e}")
    
    def get_optimization_suggestions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent optimization suggestions with optional limit."""
        return self.optimization_history[-limit:] if self.optimization_history else []
    
    def get_estimated_total_savings(self) -> Dict[str, float]:
        """Calculate total estimated savings across all suggestions."""
        total_monthly = 0.0
        
        for suggestion in self.optimization_history:
            savings = suggestion.get("estimated_savings", {})
            if isinstance(savings, dict) and "total_monthly" in savings:
                total_monthly += savings["total_monthly"]
        
        return {
            "monthly": round(total_monthly, 2),
            "annual": round(total_monthly * 12, 2)
        }
    
    def _generate_mock_metrics(self):
        """Generate mock metrics for testing."""
        import random
        
        timestamp = datetime.now().isoformat()
        
        # Generate mock pod metrics
        namespaces = ["default", "kube-system", "application", "monitoring"]
        
        # Clear previous metrics and create new ones
        self.metrics_history = {}
        
        # Generate mock pod data
        for i in range(20):
            pod_id = f"pod-{i}"
            namespace = random.choice(namespaces)
            
            # Random but reasonable resource values
            cpu_request = random.uniform(0.1, 1.0)
            memory_request = random.uniform(128, 1024) * 1024 * 1024  # 128MB to 1GB
            cpu_limit = cpu_request * random.uniform(1.5, 3.0)
            memory_limit = memory_request * random.uniform(1.5, 3.0)
            
            # Usage is sometimes much lower than request (opportunity for optimization)
            usage_factor = random.choice([0.1, 0.2, 0.3, 0.5, 0.7, 0.9])
            cpu_usage = cpu_request * usage_factor
            memory_usage = memory_request * usage_factor
            
            self.metrics_history[pod_id] = []
            
            # Generate history for the past metrics_window days
            for day in range(self.metrics_window):
                past_date = datetime.now() - timedelta(days=day)
                past_timestamp = past_date.isoformat()
                
                # Add some variation but keep the overall pattern
                daily_cpu_variation = random.uniform(0.8, 1.2)
                daily_memory_variation = random.uniform(0.8, 1.2)
                
                self.metrics_history[pod_id].append({
                    "timestamp": past_timestamp,
                    "cpu_usage": cpu_usage * daily_cpu_variation,
                    "memory_usage": memory_usage * daily_memory_variation,
                    "cpu_request": cpu_request,
                    "memory_request": memory_request,
                    "cpu_limit": cpu_limit,
                    "memory_limit": memory_limit,
                    "namespace": namespace,
                    "name": f"{namespace}-pod-{i}"
                })
        
        # Generate mock node data
        for i in range(3):
            node_id = f"node-{i}"
            
            # Random but reasonable node capacities
            cpu_capacity = 8  # 8 cores
            memory_capacity = 32 * 1024 * 1024 * 1024  # 32 GB
            
            # Usage is sometimes much lower than capacity (opportunity for optimization)
            usage_factor = random.choice([0.3, 0.4, 0.5, 0.6, 0.8])
            cpu_usage = cpu_capacity * usage_factor
            memory_usage = memory_capacity * usage_factor
            pods_running = random.randint(5, 20)
            
            self.metrics_history[node_id] = []
            
            # Generate history for the past metrics_window days
            for day in range(self.metrics_window):
                past_date = datetime.now() - timedelta(days=day)
                past_timestamp = past_date.isoformat()
                
                # Add some variation but keep the overall pattern
                daily_cpu_variation = random.uniform(0.8, 1.2)
                daily_memory_variation = random.uniform(0.8, 1.2)
                
                self.metrics_history[node_id].append({
                    "timestamp": past_timestamp,
                    "cpu_usage": cpu_usage * daily_cpu_variation,
                    "memory_usage": memory_usage * daily_memory_variation,
                    "cpu_capacity": cpu_capacity,
                    "memory_capacity": memory_capacity,
                    "pods_running": pods_running,
                    "instance_type": random.choice(["t3.large", "m5.large", "m5.xlarge"]),
                    "name": f"node-{i}"
                })
        
        logger.debug("Generated mock metrics for cost optimization analysis") 