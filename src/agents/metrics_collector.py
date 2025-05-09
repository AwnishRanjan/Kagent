"""
Kubernetes Metrics Collector

This module provides functionality for collecting metrics from Kubernetes clusters
to support prediction and analysis capabilities.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
from pathlib import Path
import json

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class KubernetesMetricsCollector:
    """
    Collects metrics from Kubernetes clusters for analysis and prediction.
    
    This collector gathers various metrics including:
    - Node resource usage (CPU, memory, disk)
    - Pod status and resource consumption
    - Network I/O statistics
    - Pressure conditions
    - Custom metrics from metrics-server
    """
    
    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        collection_interval: int = 60,
        metrics_history_file: Optional[str] = None,
        use_mock: bool = False
    ):
        """
        Initialize the metrics collector.
        
        Args:
            kubeconfig_path: Optional path to kubeconfig file
            collection_interval: How often to collect metrics, in seconds
            metrics_history_file: Optional path to store metrics history
            use_mock: Use mock data instead of real Kubernetes cluster
        """
        self.collection_interval = collection_interval
        self.metrics_history_file = metrics_history_file
        self.use_mock = use_mock
        self.running = False
        self.collection_thread = None
        self.metrics_history = []
        self.max_history_size = 1000
        
        if self.use_mock:
            # Mock mode, no real Kubernetes client
            logger.info("Using mock Kubernetes data mode")
            self.v1 = None
            self.metrics_api = None
        else:
            try:
                # Initialize Kubernetes client with better error handling
                logger.info("Initializing Kubernetes client...")
                
                if kubeconfig_path:
                    logger.info(f"Using kubeconfig from provided path: {kubeconfig_path}")
                    config.load_kube_config(config_file=kubeconfig_path)
                else:
                    try:
                        # Try default kubeconfig location first
                        logger.info("Attempting to load default kubeconfig...")
                        config.load_kube_config()
                        logger.info("Successfully loaded kubeconfig from default location")
                    except config.config_exception.ConfigException as e:
                        logger.warning(f"Could not load default kubeconfig: {e}")
                        
                        try:
                            # Try in-cluster config (for running inside a pod)
                            logger.info("Attempting to load in-cluster config...")
                            config.load_incluster_config()
                            logger.info("Successfully loaded in-cluster config")
                        except config.config_exception.ConfigException as e:
                            error_msg = f"Could not load in-cluster config: {e}"
                            logger.error(error_msg)
                            raise ValueError(f"Failed to initialize Kubernetes client. {error_msg}")
                
                # Initialize API clients
                self.v1 = client.CoreV1Api()
                self.metrics_api = client.CustomObjectsApi()
                
                # Test connection
                logger.info("Testing Kubernetes API connection...")
                try:
                    # Simple API call to validate connection
                    version = self.v1.get_api_resources()
                    logger.info(f"Successfully connected to Kubernetes API (server version: {client.VersionApi().get_code().git_version})")
                except Exception as e:
                    error_msg = f"Failed to connect to Kubernetes API: {e}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                    
            except Exception as e:
                error_msg = f"Failed to initialize Kubernetes client: {e}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        self._load_metrics_history()
    
    def _load_metrics_history(self):
        """Load metrics history from file."""
        if not self.metrics_history_file:
            return
        
        try:
            history_file = Path(self.metrics_history_file)
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            if history_file.exists():
                with open(history_file, "r") as f:
                    self.metrics_history = json.load(f)
            else:
                self.metrics_history = []
            
            logger.debug(f"Loaded metrics history from {self.metrics_history_file}")
        except Exception as e:
            logger.error(f"Error loading metrics history: {e}")
    
    def start_collection_loop(self):
        """Start the background metrics collection loop."""
        if self.running:
            logger.warning("Collection loop is already running")
            return
        
        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        logger.info("Started metrics collection loop")
    
    def stop_collection_loop(self):
        """Stop the background metrics collection loop."""
        if not self.running:
            logger.warning("Collection loop is not running")
            return
        
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5.0)
        
        # Save metrics history if configured
        if self.metrics_history_file:
            self._save_metrics_history()
        
        logger.info("Stopped metrics collection loop")
    
    def _collection_loop(self):
        """Background loop for collecting metrics at regular intervals."""
        while self.running:
            try:
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Trim history if needed
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history.pop(0)
                
                # Save history periodically
                if self.metrics_history_file and len(self.metrics_history) % 10 == 0:
                    self._save_metrics_history()
                
                logger.debug("Collected metrics successfully")
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            
            time.sleep(self.collection_interval)
    
    def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect current metrics from the Kubernetes cluster.
        
        Returns:
            Dictionary containing collected metrics
        """
        if self.use_mock:
            return self._get_mock_metrics()
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": {},
            "memory_usage": {},
            "pod_restarts": {},
            "pod_status": {},
            "node_status": {},
            "disk_pressure": {},
            "memory_pressure": {},
            "pid_pressure": {},
            "network_io": {}
        }
        
        try:
            # Get node metrics
            node_metrics = self._get_node_metrics()
            
            # Format metrics for ClusterMetrics model
            for node_name, node_data in node_metrics.items():
                metrics["cpu_usage"][node_name] = node_data.get("cpu_usage", 0.0)
                metrics["memory_usage"][node_name] = node_data.get("memory_usage", 0.0)
                metrics["node_status"][node_name] = node_data.get("status", "Unknown")
                metrics["disk_pressure"][node_name] = node_data.get("pressure", {}).get("disk", False)
                metrics["memory_pressure"][node_name] = node_data.get("pressure", {}).get("memory", False)
                metrics["pid_pressure"][node_name] = node_data.get("pressure", {}).get("pid", False)
                metrics["network_io"][node_name] = node_data.get("network_io", {"in": 0.0, "out": 0.0})
            
            # Get pod metrics
            pod_metrics = self._get_pod_metrics()
            
            # Format pod metrics for ClusterMetrics model
            for pod_name, pod_data in pod_metrics.items():
                metrics["pod_restarts"][pod_name] = pod_data.get("restart_count", 0)
                metrics["pod_status"][pod_name] = pod_data.get("status", "Unknown")
            
            # Get cluster-level metrics
            cluster_metrics = self._get_cluster_metrics()
            
            # Add cluster as a "node" for average metrics
            metrics["cpu_usage"]["cluster"] = cluster_metrics.get("total_cpu_usage", 0.0)
            metrics["memory_usage"]["cluster"] = cluster_metrics.get("total_memory_usage", 0.0)
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            
            # Ensure we have default values even in case of error
            if not metrics["cpu_usage"]:
                metrics["cpu_usage"] = {"cluster": 0.0}
            if not metrics["memory_usage"]:
                metrics["memory_usage"] = {"cluster": 0.0}
            if not metrics["pod_restarts"]:
                metrics["pod_restarts"] = {"default": 0}
            if not metrics["pod_status"]:
                metrics["pod_status"] = {"default": "Unknown"}
            if not metrics["node_status"]:
                metrics["node_status"] = {"default": "Unknown"}
            if not metrics["disk_pressure"]:
                metrics["disk_pressure"] = {"default": False}
            if not metrics["memory_pressure"]:
                metrics["memory_pressure"] = {"default": False}
            if not metrics["pid_pressure"]:
                metrics["pid_pressure"] = {"default": False}
            if not metrics["network_io"]:
                metrics["network_io"] = {"default": {"in": 0.0, "out": 0.0}}
                
            metrics["error"] = str(e)
        
        return metrics
    
    def _get_node_metrics(self) -> Dict[str, Any]:
        """Collect metrics for all nodes in the cluster."""
        node_metrics = {}
        
        try:
            # Get node information
            nodes = self.v1.list_node()
            
            for node in nodes.items:
                node_name = node.metadata.name
                node_metrics[node_name] = {
                    "cpu_usage": 0.0,
                    "memory_usage": 0.0,
                    "disk_usage": 0.0,
                    "network_io": {"in": 0.0, "out": 0.0},
                    "pressure": {
                        "disk": False,
                        "memory": False,
                        "pid": False
                    },
                    "status": node.status.conditions[-1].type if node.status.conditions else "Unknown"
                }
            
            # Get node metrics from metrics-server
            try:
                node_metrics_data = self.metrics_api.list_cluster_custom_object(
                    "metrics.k8s.io", "v1beta1", "nodes"
                )
                
                for metric in node_metrics_data["items"]:
                    node_name = metric["metadata"]["name"]
                    if node_name in node_metrics:
                        # Convert resource usage to percentages
                        node_info = self.v1.read_node(node_name)
                        cpu_capacity = self._parse_resource_quantity(node_info.status.capacity["cpu"])
                        memory_capacity = self._parse_resource_quantity(node_info.status.capacity["memory"])
                        
                        cpu_usage = self._parse_resource_quantity(metric["usage"]["cpu"])
                        memory_usage = self._parse_resource_quantity(metric["usage"]["memory"])
                        
                        node_metrics[node_name]["cpu_usage"] = (cpu_usage / cpu_capacity) * 100
                        node_metrics[node_name]["memory_usage"] = (memory_usage / memory_capacity) * 100
            except ApiException as e:
                logger.warning(f"Could not get node metrics from metrics-server: {e}")
            
            # Get node pressure conditions
            for node in nodes.items:
                node_name = node.metadata.name
                for condition in node.status.conditions:
                    if condition.type == "DiskPressure":
                        node_metrics[node_name]["pressure"]["disk"] = condition.status == "True"
                    elif condition.type == "MemoryPressure":
                        node_metrics[node_name]["pressure"]["memory"] = condition.status == "True"
                    elif condition.type == "PIDPressure":
                        node_metrics[node_name]["pressure"]["pid"] = condition.status == "True"
            
        except Exception as e:
            logger.error(f"Error getting node metrics: {e}")
        
        return node_metrics
    
    def _get_pod_metrics(self) -> Dict[str, Any]:
        """Collect metrics for all pods in the cluster."""
        pod_metrics = {}
        
        try:
            # Get pod information
            pods = self.v1.list_pod_for_all_namespaces()
            
            for pod in pods.items:
                pod_name = f"{pod.metadata.namespace}/{pod.metadata.name}"
                pod_metrics[pod_name] = {
                    "cpu_usage": 0.0,
                    "memory_usage": 0.0,
                    "restart_count": sum(container.restart_count for container in pod.status.container_statuses or []),
                    "status": pod.status.phase,
                    "containers": {}
                }
                
                # Get container metrics
                for container in pod.spec.containers:
                    pod_metrics[pod_name]["containers"][container.name] = {
                        "cpu_usage": 0.0,
                        "memory_usage": 0.0,
                        "restart_count": 0
                    }
            
            # Get pod metrics from metrics-server
            try:
                pod_metrics_data = self.metrics_api.list_cluster_custom_object(
                    "metrics.k8s.io", "v1beta1", "pods"
                )
                
                for metric in pod_metrics_data["items"]:
                    pod_name = f"{metric['metadata']['namespace']}/{metric['metadata']['name']}"
                    if pod_name in pod_metrics:
                        for container in metric["containers"]:
                            container_name = container["name"]
                            if container_name in pod_metrics[pod_name]["containers"]:
                                # Convert resource usage to percentages
                                pod_info = self.v1.read_namespaced_pod(
                                    metric["metadata"]["name"],
                                    metric["metadata"]["namespace"]
                                )
                                
                                # Find container spec
                                container_spec = next(
                                    (c for c in pod_info.spec.containers if c.name == container_name),
                                    None
                                )
                                
                                if container_spec:
                                    cpu_limit = self._parse_resource_quantity(container_spec.resources.limits.get("cpu", "0"))
                                    memory_limit = self._parse_resource_quantity(container_spec.resources.limits.get("memory", "0"))
                                    
                                    cpu_usage = self._parse_resource_quantity(container["usage"]["cpu"])
                                    memory_usage = self._parse_resource_quantity(container["usage"]["memory"])
                                    
                                    if cpu_limit > 0:
                                        pod_metrics[pod_name]["containers"][container_name]["cpu_usage"] = (cpu_usage / cpu_limit) * 100
                                    if memory_limit > 0:
                                        pod_metrics[pod_name]["containers"][container_name]["memory_usage"] = (memory_usage / memory_limit) * 100
                                    
                                    # Update pod-level metrics
                                    pod_metrics[pod_name]["cpu_usage"] += pod_metrics[pod_name]["containers"][container_name]["cpu_usage"]
                                    pod_metrics[pod_name]["memory_usage"] += pod_metrics[pod_name]["containers"][container_name]["memory_usage"]
            except ApiException as e:
                logger.warning(f"Could not get pod metrics from metrics-server: {e}")
            
        except Exception as e:
            logger.error(f"Error getting pod metrics: {e}")
        
        return pod_metrics
    
    def _get_cluster_metrics(self) -> Dict[str, Any]:
        """Collect cluster-level metrics."""
        cluster_metrics = {
            "total_nodes": 0,
            "ready_nodes": 0,
            "total_pods": 0,
            "running_pods": 0,
            "pending_pods": 0,
            "failed_pods": 0,
            "total_cpu_usage": 0.0,
            "total_memory_usage": 0.0
        }
        
        try:
            # Get node information
            nodes = self.v1.list_node()
            cluster_metrics["total_nodes"] = len(nodes.items)
            cluster_metrics["ready_nodes"] = sum(
                1 for node in nodes.items
                if any(cond.type == "Ready" and cond.status == "True" for cond in node.status.conditions)
            )
            
            # Get pod information
            pods = self.v1.list_pod_for_all_namespaces()
            cluster_metrics["total_pods"] = len(pods.items)
            cluster_metrics["running_pods"] = sum(1 for pod in pods.items if pod.status.phase == "Running")
            cluster_metrics["pending_pods"] = sum(1 for pod in pods.items if pod.status.phase == "Pending")
            cluster_metrics["failed_pods"] = sum(1 for pod in pods.items if pod.status.phase == "Failed")
            
            # Calculate total resource usage
            total_cpu_usage = 0.0
            total_memory_usage = 0.0
            node_count = 0
            
            for node in nodes.items:
                try:
                    node_metrics = self.metrics_api.get_cluster_custom_object(
                        "metrics.k8s.io", "v1beta1", "nodes", node.metadata.name
                    )
                    
                    cpu_capacity = self._parse_resource_quantity(node.status.capacity["cpu"])
                    memory_capacity = self._parse_resource_quantity(node.status.capacity["memory"])
                    
                    cpu_usage = self._parse_resource_quantity(node_metrics["usage"]["cpu"])
                    memory_usage = self._parse_resource_quantity(node_metrics["usage"]["memory"])
                    
                    if cpu_capacity > 0:
                        total_cpu_usage += (cpu_usage / cpu_capacity) * 100
                    if memory_capacity > 0:
                        total_memory_usage += (memory_usage / memory_capacity) * 100
                    
                    node_count += 1
                except ApiException:
                    continue
            
            if node_count > 0:
                cluster_metrics["total_cpu_usage"] = total_cpu_usage / node_count
                cluster_metrics["total_memory_usage"] = total_memory_usage / node_count
            
        except Exception as e:
            logger.error(f"Error getting cluster metrics: {e}")
        
        return cluster_metrics
    
    def _parse_resource_quantity(self, quantity: str) -> float:
        """Parse Kubernetes resource quantity string into a float value."""
        try:
            if quantity.endswith("m"):
                return float(quantity[:-1]) / 1000
            elif quantity.endswith("Ki"):
                return float(quantity[:-2]) * 1024
            elif quantity.endswith("Mi"):
                return float(quantity[:-2]) * 1024 * 1024
            elif quantity.endswith("Gi"):
                return float(quantity[:-2]) * 1024 * 1024 * 1024
            else:
                return float(quantity)
        except (ValueError, TypeError):
            return 0.0
    
    def _save_metrics_history(self):
        """Save metrics history to file."""
        if not self.metrics_history_file:
            return
        
        try:
            history_file = Path(self.metrics_history_file)
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(history_file, "w") as f:
                json.dump(self.metrics_history, f, indent=2)
            
            logger.debug(f"Saved metrics history to {self.metrics_history_file}")
        except Exception as e:
            logger.error(f"Error saving metrics history: {e}")
    
    def get_formatted_metrics(self) -> Dict[str, Any]:
        """
        Get the latest metrics in a format suitable for the predictor.
        
        Returns:
            Dictionary containing formatted metrics
        """
        if not self.metrics_history:
            return {}
        
        latest_metrics = self.metrics_history[-1]
        
        # Make sure nodes and pods dictionaries exist
        nodes = latest_metrics.get("nodes", {})
        pods = latest_metrics.get("pods", {})
        
        # Create formatted metrics with empty dictionaries as fallbacks
        formatted_metrics = {
            "cpu_usage": {},
            "memory_usage": {},
            "pod_restarts": {},
            "pod_status": {},
            "node_status": {},
            "disk_pressure": {},
            "memory_pressure": {},
            "pid_pressure": {},
            "network_io": {}
        }
        
        # Populate dictionaries with data if available
        for node, data in nodes.items():
            formatted_metrics["cpu_usage"][node] = data.get("cpu_usage", 0)
            formatted_metrics["memory_usage"][node] = data.get("memory_usage", 0)
            formatted_metrics["node_status"][node] = data.get("status", "Unknown")
            
            # Handle pressure conditions with fallbacks
            pressure = data.get("pressure", {})
            formatted_metrics["disk_pressure"][node] = pressure.get("disk", False)
            formatted_metrics["memory_pressure"][node] = pressure.get("memory", False)
            formatted_metrics["pid_pressure"][node] = pressure.get("pid", False)
            
            formatted_metrics["network_io"][node] = data.get("network_io", {"in": 0, "out": 0})
        
        # Populate pod data
        for pod, data in pods.items():
            formatted_metrics["pod_restarts"][pod] = data.get("restart_count", 0)
            formatted_metrics["pod_status"][pod] = data.get("status", "Unknown")
        
        return formatted_metrics
    
    def _get_mock_metrics(self) -> Dict[str, Any]:
        """Generate mock metrics for testing."""
        import random
        
        # Generate mock nodes
        node_count = random.randint(1, 5)
        nodes_dict = {}
        for i in range(node_count):
            node_name = f"mock-node-{i}"
            nodes_dict[node_name] = {
                "cpu_usage": random.uniform(10, 90),
                "memory_usage": random.uniform(20, 80),
                "disk_usage": random.uniform(30, 70),
                "network_io": {
                    "in": random.uniform(1000, 10000),
                    "out": random.uniform(1000, 10000)
                },
                "pressure": {
                    "disk": random.random() > 0.9,
                    "memory": random.random() > 0.95,
                    "pid": random.random() > 0.98
                },
                "status": random.choice(["Ready", "NotReady"]) if random.random() > 0.9 else "Ready"
            }
        
        # Generate mock pods
        pod_count = random.randint(3, 15)
        pods_dict = {}
        for i in range(pod_count):
            pod_name = f"mock-pod-{i}"
            pods_dict[pod_name] = {
                "namespace": random.choice(["default", "kube-system", "monitoring"]),
                "status": random.choice(["Running", "Pending", "Failed", "CrashLoopBackOff", "Succeeded"]) 
                           if random.random() > 0.9 else "Running",
                "restart_count": random.randint(0, 10) if random.random() > 0.8 else 0,
                "cpu_usage": random.uniform(5, 50),
                "memory_usage": random.uniform(10, 60)
            }
        
        # Create the complete metrics structure for ClusterMetrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": {node: data["cpu_usage"] for node, data in nodes_dict.items()},
            "memory_usage": {node: data["memory_usage"] for node, data in nodes_dict.items()},
            "pod_restarts": {pod: data["restart_count"] for pod, data in pods_dict.items()},
            "pod_status": {pod: data["status"] for pod, data in pods_dict.items()},
            "node_status": {node: data["status"] for node, data in nodes_dict.items()},
            "disk_pressure": {node: data["pressure"]["disk"] for node, data in nodes_dict.items()},
            "memory_pressure": {node: data["pressure"]["memory"] for node, data in nodes_dict.items()},
            "pid_pressure": {node: data["pressure"]["pid"] for node, data in nodes_dict.items()},
            "network_io": {node: data["network_io"] for node, data in nodes_dict.items()}
        }
        
        # Add cluster as a "node" for average metrics
        metrics["cpu_usage"]["cluster"] = sum(data["cpu_usage"] for data in nodes_dict.values()) / max(1, len(nodes_dict))
        metrics["memory_usage"]["cluster"] = sum(data["memory_usage"] for data in nodes_dict.values()) / max(1, len(nodes_dict))
        
        return metrics

    def start(self):
        """Start the metrics collection. Alias for start_collection_loop."""
        self.start_collection_loop()

    def stop(self):
        """Stop the metrics collection. Alias for stop_collection_loop."""
        self.stop_collection_loop() 