"""
Kubernetes Security Scanner Agent

This module provides security scanning capabilities for Kubernetes clusters,
identifying vulnerabilities, misconfigurations, and security risks.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
import time
import json
from pathlib import Path

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class SecurityScanResult:
    """Model representing security scan results"""
    def __init__(self, 
                 timestamp: str,
                 vulnerabilities: List[Dict[str, Any]],
                 misconfigurations: List[Dict[str, Any]],
                 compliance_issues: List[Dict[str, Any]]):
        self.timestamp = timestamp
        self.vulnerabilities = vulnerabilities
        self.misconfigurations = misconfigurations
        self.compliance_issues = compliance_issues
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "vulnerabilities": self.vulnerabilities,
            "misconfigurations": self.misconfigurations,
            "compliance_issues": self.compliance_issues,
            "total_issues": len(self.vulnerabilities) + len(self.misconfigurations) + len(self.compliance_issues)
        }

class KubernetesSecurityScanner:
    """
    Provides security scanning capabilities for Kubernetes clusters.
    
    This scanner identifies:
    - Vulnerabilities in workloads
    - Security misconfigurations
    - Compliance issues
    - Role-based access control (RBAC) problems
    - Network policy gaps
    """
    
    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        scan_interval: int = 3600,  # Default: scan hourly
        history_file: Optional[str] = None,
        use_mock: bool = False
    ):
        """
        Initialize the security scanner.
        
        Args:
            kubeconfig_path: Optional path to kubeconfig file
            scan_interval: How often to perform scans, in seconds
            history_file: Optional path to store scan history
            use_mock: Whether to use mock data instead of connecting to a real Kubernetes cluster
        """
        self.scan_interval = scan_interval
        self.history_file = history_file
        self.scan_history = []
        self.max_history_size = 100
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
                self.rbac_v1 = client.RbacAuthorizationV1Api()
                self.networking_v1 = client.NetworkingV1Api()
                logger.info("Successfully initialized Kubernetes client for security scanning")
            except Exception as e:
                logger.error(f"Failed to initialize Kubernetes client: {e}")
                raise
        else:
            # In mock mode, set API clients to None
            logger.info("Initializing security scanner in mock mode")
            self.core_v1 = None
            self.apps_v1 = None
            self.rbac_v1 = None
            self.networking_v1 = None
        
        # Scanning state
        self.running = False
        self.scan_thread = None
    
    def start_scanning_loop(self):
        """Start the background security scanning loop."""
        if self.running:
            logger.warning("Security scanning loop is already running")
            return
        
        self.running = True
        self.scan_thread = threading.Thread(target=self._scanning_loop)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        logger.info("Started security scanning loop")
    
    def stop_scanning_loop(self):
        """Stop the background security scanning loop."""
        if not self.running:
            logger.warning("Security scanning loop is not running")
            return
        
        self.running = False
        if self.scan_thread:
            self.scan_thread.join(timeout=5.0)
        
        # Save scan history if configured
        if self.history_file:
            self._save_scan_history()
        
        logger.info("Stopped security scanning loop")
    
    def _scanning_loop(self):
        """Background loop for performing security scans at regular intervals."""
        while self.running:
            try:
                scan_result = self.perform_security_scan()
                self.scan_history.append(scan_result.to_dict())
                
                # Trim history if needed
                if len(self.scan_history) > self.max_history_size:
                    self.scan_history.pop(0)
                
                # Save history
                if self.history_file:
                    self._save_scan_history()
                
                logger.info(f"Completed security scan, found {scan_result.to_dict()['total_issues']} issues")
            except Exception as e:
                logger.error(f"Error performing security scan: {e}")
            
            time.sleep(self.scan_interval)
    
    def perform_security_scan(self) -> SecurityScanResult:
        """
        Perform a comprehensive security scan of the Kubernetes cluster.
        
        Returns:
            SecurityScanResult containing identified issues
        """
        timestamp = datetime.now().isoformat()
        
        if self.use_mock:
            # Generate mock scan results when in mock mode
            vulnerabilities = self._generate_mock_vulnerabilities()
            misconfigurations = self._generate_mock_misconfigurations()
            compliance_issues = self._generate_mock_compliance_issues()
        else:
            # Scan for different security issues using the actual K8s APIs
            vulnerabilities = self._scan_for_vulnerabilities()
            misconfigurations = self._scan_for_misconfigurations()
            compliance_issues = self._scan_for_compliance_issues()
        
        return SecurityScanResult(
            timestamp=timestamp,
            vulnerabilities=vulnerabilities,
            misconfigurations=misconfigurations,
            compliance_issues=compliance_issues
        )
    
    def _scan_for_vulnerabilities(self) -> List[Dict[str, Any]]:
        """
        Scan for vulnerabilities in workloads.
        
        This includes:
        - Containers running with known vulnerable images
        - Outdated container images
        - Containers using deprecated APIs
        
        Returns:
            List of identified vulnerabilities
        """
        vulnerabilities = []
        
        try:
            # Scan pods across all namespaces
            pods = self.core_v1.list_pod_for_all_namespaces()
            
            for pod in pods.items:
                namespace = pod.metadata.namespace
                pod_name = pod.metadata.name
                
                # Check containers in pod
                for container in pod.spec.containers:
                    # Check for 'latest' tag (not recommended for production)
                    if container.image.endswith(':latest'):
                        vulnerabilities.append({
                            "type": "image_tag_latest",
                            "severity": "medium",
                            "resource_type": "Pod",
                            "namespace": namespace,
                            "name": pod_name,
                            "container": container.name,
                            "image": container.image,
                            "description": "Using 'latest' tag in production is not recommended as it makes tracking and rollbacks difficult",
                            "remediation": "Use specific version tags for container images"
                        })
                    
                    # Check for privileged containers
                    if container.security_context and container.security_context.privileged:
                        vulnerabilities.append({
                            "type": "privileged_container",
                            "severity": "high",
                            "resource_type": "Pod",
                            "namespace": namespace,
                            "name": pod_name,
                            "container": container.name,
                            "description": "Container is running in privileged mode, which gives it full access to the host",
                            "remediation": "Avoid using privileged containers; use more limited security contexts"
                        })
            
            # Additional vulnerability scanning logic would go here...
            
        except ApiException as e:
            logger.error(f"Error scanning for vulnerabilities: {e}")
        
        return vulnerabilities
    
    def _scan_for_misconfigurations(self) -> List[Dict[str, Any]]:
        """
        Scan for security misconfigurations.
        
        This includes:
        - Pods running as root
        - Missing resource limits
        - Exposed services
        - Misconfigured network policies
        
        Returns:
            List of identified misconfigurations
        """
        misconfigurations = []
        
        try:
            # Scan for pods without resource limits
            pods = self.core_v1.list_pod_for_all_namespaces()
            
            for pod in pods.items:
                namespace = pod.metadata.namespace
                pod_name = pod.metadata.name
                
                for container in pod.spec.containers:
                    # Check for missing resource limits
                    if not container.resources or not container.resources.limits:
                        misconfigurations.append({
                            "type": "missing_resource_limits",
                            "severity": "medium",
                            "resource_type": "Pod",
                            "namespace": namespace,
                            "name": pod_name,
                            "container": container.name,
                            "description": "Container is missing resource limits, which could lead to resource exhaustion",
                            "remediation": "Set appropriate CPU and memory limits"
                        })
                    
                    # Check for running as root
                    if (not container.security_context or 
                        not container.security_context.run_as_non_root or
                        container.security_context.run_as_user == 0):
                        misconfigurations.append({
                            "type": "run_as_root",
                            "severity": "medium",
                            "resource_type": "Pod",
                            "namespace": namespace,
                            "name": pod_name,
                            "container": container.name,
                            "description": "Container is running as root, which is a security risk",
                            "remediation": "Set runAsNonRoot: true and specify a non-zero user ID"
                        })
            
            # Additional misconfiguration scanning logic would go here...
            
        except ApiException as e:
            logger.error(f"Error scanning for misconfigurations: {e}")
        
        return misconfigurations
    
    def _scan_for_compliance_issues(self) -> List[Dict[str, Any]]:
        """
        Scan for compliance issues.
        
        This includes:
        - RBAC permissions that are too broad
        - Lack of network policies
        - Namespaces without quotas
        - Use of default service accounts
        
        Returns:
            List of identified compliance issues
        """
        compliance_issues = []
        
        try:
            # Scan namespaces for missing network policies
            namespaces = self.core_v1.list_namespace()
            network_policies = {
                policy.metadata.namespace: True 
                for policy in self.networking_v1.list_network_policy_for_all_namespaces().items
            }
            
            for namespace in namespaces.items:
                namespace_name = namespace.metadata.name
                
                # Skip system namespaces
                if namespace_name in ["kube-system", "kube-public", "kube-node-lease"]:
                    continue
                
                # Check for missing network policies
                if namespace_name not in network_policies:
                    compliance_issues.append({
                        "type": "no_network_policy",
                        "severity": "medium",
                        "resource_type": "Namespace",
                        "namespace": namespace_name,
                        "name": namespace_name,
                        "description": "Namespace does not have any Network Policies, allowing unrestricted pod-to-pod communication",
                        "remediation": "Apply appropriate Network Policies to restrict pod communication"
                    })
                
                # Check for secrets with plaintext sensitive data
                secrets = self.core_v1.list_namespaced_secret(namespace_name)
                for secret in secrets.items:
                    # Skip service account tokens and other system secrets
                    if secret.type in ["kubernetes.io/service-account-token", "kubernetes.io/dockerconfigjson"]:
                        continue
                    
                    compliance_issues.append({
                        "type": "plaintext_secrets",
                        "severity": "high",
                        "resource_type": "Secret",
                        "namespace": namespace_name,
                        "name": secret.metadata.name,
                        "description": "Secrets should be managed by a dedicated secret management solution rather than Kubernetes",
                        "remediation": "Use a dedicated secret management solution like HashiCorp Vault, AWS Secrets Manager, etc."
                    })
            
            # Additional compliance scanning logic would go here...
            
        except ApiException as e:
            logger.error(f"Error scanning for compliance issues: {e}")
        
        return compliance_issues
    
    def _generate_mock_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Generate mock vulnerability data for testing purposes."""
        import random
        
        mock_vulnerabilities = []
        severities = ["critical", "high", "medium", "low"]
        namespaces = ["default", "kube-system", "application", "monitoring"]
        container_images = [
            "nginx:latest", 
            "mysql:5.6", 
            "wordpress:4.9", 
            "redis:3.2",
            "mongodb:3.4",
            "elasticsearch:6.4.2"
        ]
        
        # Generate 3-8 random vulnerabilities
        for i in range(random.randint(3, 8)):
            severity = random.choice(severities)
            namespace = random.choice(namespaces)
            image = random.choice(container_images)
            
            mock_vulnerabilities.append({
                "type": "outdated_image" if ":" in image else "image_tag_latest",
                "severity": severity,
                "resource_type": "Pod",
                "namespace": namespace,
                "name": f"pod-{random.randint(1, 50)}",
                "container": f"container-{random.randint(1, 5)}",
                "image": image,
                "description": f"Using {image} which may contain security vulnerabilities",
                "remediation": "Update to the latest patched version"
            })
        
        return mock_vulnerabilities

    def _generate_mock_misconfigurations(self) -> List[Dict[str, Any]]:
        """Generate mock misconfigurations data for testing purposes."""
        import random
        
        mock_misconfigurations = []
        severities = ["critical", "high", "medium", "low"]
        namespaces = ["default", "kube-system", "application", "monitoring"]
        
        # Generate 2-6 random misconfigurations
        for i in range(random.randint(2, 6)):
            severity = random.choice(severities)
            namespace = random.choice(namespaces)
            
            mock_misconfigurations.append({
                "type": random.choice([
                    "privileged_container", 
                    "host_network", 
                    "host_pid", 
                    "missing_resource_limits",
                    "run_as_root"
                ]),
                "severity": severity,
                "resource_type": random.choice(["Pod", "Deployment", "StatefulSet", "DaemonSet"]),
                "namespace": namespace,
                "name": f"{namespace}-resource-{random.randint(1, 50)}",
                "description": "Security misconfiguration detected",
                "remediation": "Apply security best practices"
            })
        
        return mock_misconfigurations

    def _generate_mock_compliance_issues(self) -> List[Dict[str, Any]]:
        """Generate mock compliance issues data for testing purposes."""
        import random
        
        mock_compliance_issues = []
        severities = ["critical", "high", "medium", "low"]
        namespaces = ["default", "kube-system", "application", "monitoring"]
        
        # Generate 2-5 random compliance issues
        for i in range(random.randint(2, 5)):
            severity = random.choice(severities)
            namespace = random.choice(namespaces)
            
            mock_compliance_issues.append({
                "type": random.choice([
                    "no_network_policy", 
                    "overly_permissive_rbac", 
                    "missing_pod_security_policy",
                    "plaintext_secrets"
                ]),
                "severity": severity,
                "resource_type": random.choice(["Namespace", "Role", "RoleBinding", "Secret"]),
                "namespace": namespace,
                "name": f"{namespace}-{random.randint(1, 50)}",
                "description": "Compliance issue detected",
                "remediation": "Apply compliance controls"
            })
        
        return mock_compliance_issues
    
    def _save_scan_history(self):
        """Save scan history to file."""
        if not self.history_file:
            return
        
        try:
            history_file = Path(self.history_file)
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(history_file, "w") as f:
                json.dump(self.scan_history, f, indent=2)
            
            logger.debug(f"Saved scan history to {self.history_file}")
        except Exception as e:
            logger.error(f"Error saving scan history: {e}")
    
    def get_latest_scan_results(self) -> Optional[Dict[str, Any]]:
        """Get the most recent scan results."""
        return self.scan_history[-1] if self.scan_history else None
    
    def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get scan history, limited to the specified number of entries."""
        return self.scan_history[-limit:] if self.scan_history else [] 