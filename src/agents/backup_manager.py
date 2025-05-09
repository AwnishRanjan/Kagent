"""
Kubernetes Backup Manager Agent

This module provides backup and recovery capabilities for Kubernetes resources,
enabling disaster recovery and resource versioning.
"""

import logging
import json
import os
import time
import yaml
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
import tarfile
import threading
from typing import Dict, List, Any, Optional, Set

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class BackupJob:
    """Model representing a backup job"""
    def __init__(self, 
                 id: str,
                 name: str,
                 namespaces: List[str],
                 resource_types: List[str],
                 include_labels: Optional[Dict[str, str]] = None,
                 exclude_labels: Optional[Dict[str, str]] = None,
                 backup_location: str = "local",
                 timestamp: Optional[str] = None,
                 status: str = "pending"):
        self.id = id
        self.name = name
        self.namespaces = namespaces
        self.resource_types = resource_types
        self.include_labels = include_labels or {}
        self.exclude_labels = exclude_labels or {}
        self.backup_location = backup_location  # "local", "s3", etc.
        self.timestamp = timestamp or datetime.now().isoformat()
        self.status = status  # "pending", "running", "completed", "failed"
        self.resources_backed_up: Dict[str, int] = {}
        self.file_size: Optional[int] = None
        self.error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "namespaces": self.namespaces,
            "resource_types": self.resource_types,
            "include_labels": self.include_labels,
            "exclude_labels": self.exclude_labels,
            "backup_location": self.backup_location,
            "timestamp": self.timestamp,
            "status": self.status,
            "resources_backed_up": self.resources_backed_up,
            "file_size": self.file_size,
            "error_message": self.error_message
        }

class RestoreJob:
    """Model representing a restore job"""
    def __init__(self,
                 id: str,
                 backup_id: str,
                 name: str,
                 namespaces: List[str],
                 resource_types: Optional[List[str]] = None,
                 include_labels: Optional[Dict[str, str]] = None,
                 exclude_labels: Optional[Dict[str, str]] = None,
                 restore_strategy: str = "create_or_replace",
                 timestamp: Optional[str] = None,
                 status: str = "pending"):
        self.id = id
        self.backup_id = backup_id
        self.name = name
        self.namespaces = namespaces
        self.resource_types = resource_types  # If None, restore all from backup
        self.include_labels = include_labels or {}
        self.exclude_labels = exclude_labels or {}
        self.restore_strategy = restore_strategy  # "create_or_replace", "create_only", "replace_only"
        self.timestamp = timestamp or datetime.now().isoformat()
        self.status = status  # "pending", "running", "completed", "failed"
        self.resources_restored: Dict[str, int] = {}
        self.error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "backup_id": self.backup_id,
            "name": self.name,
            "namespaces": self.namespaces,
            "resource_types": self.resource_types,
            "include_labels": self.include_labels,
            "exclude_labels": self.exclude_labels,
            "restore_strategy": self.restore_strategy,
            "timestamp": self.timestamp,
            "status": self.status,
            "resources_restored": self.resources_restored,
            "error_message": self.error_message
        }

class KubernetesBackupManager:
    """
    Provides backup and recovery capabilities for Kubernetes resources.
    
    This manager:
    - Creates backups of specified Kubernetes resources
    - Stores backups in local or remote storage
    - Restores resources from backups
    - Manages backup retention and scheduling
    """
    
    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        backup_dir: str = "~/.kagent/backups",
        max_backups: int = 10,
        history_file: Optional[str] = None,
        use_mock: bool = False
    ):
        """
        Initialize the backup manager.
        
        Args:
            kubeconfig_path: Optional path to kubeconfig file
            backup_dir: Directory to store backups
            max_backups: Maximum number of backups to keep
            history_file: Optional path to store backup/restore history
            use_mock: Whether to use mock data instead of connecting to a real Kubernetes cluster
        """
        self.backup_dir = os.path.expanduser(backup_dir)
        self.max_backups = max_backups
        self.history_file = history_file
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
                self.batch_v1 = client.BatchV1Api()
                self.networking_v1 = client.NetworkingV1Api()
                self.rbac_v1 = client.RbacAuthorizationV1Api()
                self.storage_v1 = client.StorageV1Api()
                self.custom_objects = client.CustomObjectsApi()
                logger.info("Successfully initialized Kubernetes client for backup manager")
            except Exception as e:
                logger.error(f"Failed to initialize Kubernetes client: {e}")
                raise
        else:
            # In mock mode, set API clients to None
            logger.info("Initializing backup manager in mock mode")
            self.core_v1 = None
            self.apps_v1 = None
            self.batch_v1 = None
            self.networking_v1 = None
            self.rbac_v1 = None
            self.storage_v1 = None
            self.custom_objects = None
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize history storage
        self.backup_jobs: List[BackupJob] = []
        self.restore_jobs: List[RestoreJob] = []
        
        # Load history if available
        if history_file:
            self._load_history()
        
        # In mock mode, create some sample backup/restore data
        if use_mock and not self.backup_jobs:
            self._generate_mock_backup_data()
    
    def _load_history(self):
        """Load backup and restore history from file."""
        if not self.history_file or not os.path.exists(self.history_file):
            return
        
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
                
                if "backup_jobs" in history:
                    for job_dict in history["backup_jobs"]:
                        job = BackupJob(
                            id=job_dict["id"],
                            name=job_dict["name"],
                            namespaces=job_dict["namespaces"],
                            resource_types=job_dict["resource_types"],
                            include_labels=job_dict.get("include_labels"),
                            exclude_labels=job_dict.get("exclude_labels"),
                            backup_location=job_dict["backup_location"],
                            timestamp=job_dict["timestamp"],
                            status=job_dict["status"]
                        )
                        job.resources_backed_up = job_dict.get("resources_backed_up", {})
                        job.file_size = job_dict.get("file_size")
                        job.error_message = job_dict.get("error_message")
                        self.backup_jobs.append(job)
                
                if "restore_jobs" in history:
                    for job_dict in history["restore_jobs"]:
                        job = RestoreJob(
                            id=job_dict["id"],
                            backup_id=job_dict["backup_id"],
                            name=job_dict["name"],
                            namespaces=job_dict["namespaces"],
                            resource_types=job_dict.get("resource_types"),
                            include_labels=job_dict.get("include_labels"),
                            exclude_labels=job_dict.get("exclude_labels"),
                            restore_strategy=job_dict["restore_strategy"],
                            timestamp=job_dict["timestamp"],
                            status=job_dict["status"]
                        )
                        job.resources_restored = job_dict.get("resources_restored", {})
                        job.error_message = job_dict.get("error_message")
                        self.restore_jobs.append(job)
                
            logger.info(f"Loaded {len(self.backup_jobs)} backup jobs and {len(self.restore_jobs)} restore jobs from history")
        except Exception as e:
            logger.error(f"Error loading backup history: {e}")
    
    def _save_history(self):
        """Save backup and restore history to file."""
        if not self.history_file:
            return
        
        try:
            history = {
                "backup_jobs": [job.to_dict() for job in self.backup_jobs],
                "restore_jobs": [job.to_dict() for job in self.restore_jobs]
            }
            
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            logger.debug(f"Saved backup history to {self.history_file}")
        except Exception as e:
            logger.error(f"Error saving backup history: {e}")
    
    def create_backup(self, job: BackupJob) -> BackupJob:
        """
        Create a backup of Kubernetes resources according to the backup job specification.
        
        Args:
            job: BackupJob specification
            
        Returns:
            Updated BackupJob with results
        """
        if self.use_mock:
            return self._create_mock_backup(job)
        
        logger.info(f"Starting backup job: {job.name}")
        job.status = "running"
        self.backup_jobs.append(job)
        self._save_history()
        
        try:
            # Create a temporary directory for resources
            with tempfile.TemporaryDirectory() as temp_dir:
                total_resources = 0
                
                # Process each namespace
                for namespace in job.namespaces:
                    if namespace == "all":
                        namespaces = [ns.metadata.name for ns in self.core_v1.list_namespace().items]
                    else:
                        namespaces = [namespace]
                    
                    for ns in namespaces:
                        # Skip system namespaces if backing up "all"
                        if namespace == "all" and ns in ["kube-system", "kube-public", "kube-node-lease"]:
                            continue
                        
                        # Create directory for namespace
                        ns_dir = os.path.join(temp_dir, ns)
                        os.makedirs(ns_dir, exist_ok=True)
                        
                        # Process each resource type
                        backup_count = self._backup_resources(job, ns, ns_dir)
                        total_resources += sum(backup_count.values())
                        
                        # Add to job statistics
                        for resource_type, count in backup_count.items():
                            if resource_type not in job.resources_backed_up:
                                job.resources_backed_up[resource_type] = 0
                            job.resources_backed_up[resource_type] += count
                
                # Check if any resources were backed up
                if total_resources == 0:
                    logger.warning(f"No resources matched the backup criteria for job: {job.name}")
                
                # Create backup archive
                archive_name = f"{job.id}_{job.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
                archive_path = os.path.join(self.backup_dir, archive_name)
                
                with tarfile.open(archive_path, "w:gz") as tar:
                    # Add metadata file
                    metadata = {
                        "backup_id": job.id,
                        "name": job.name,
                        "timestamp": job.timestamp,
                        "namespaces": job.namespaces,
                        "resource_types": job.resource_types,
                        "include_labels": job.include_labels,
                        "exclude_labels": job.exclude_labels,
                        "kubeconfig_context": None,  # TODO: Add context info
                        "resources": job.resources_backed_up
                    }
                    
                    metadata_path = os.path.join(temp_dir, "metadata.json")
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    # Add all files to archive
                    tar.add(temp_dir, arcname="")
                
                # Update job with results
                job.file_size = os.path.getsize(archive_path)
                job.status = "completed"
                
                # Enforce backup retention
                self._enforce_backup_retention()
                
                logger.info(f"Backup job completed: {job.name}, backed up {total_resources} resources to {archive_path}")
        
        except Exception as e:
            logger.error(f"Error during backup job {job.name}: {e}")
            job.status = "failed"
            job.error_message = str(e)
        
        # Save updated history
        self._save_history()
        
        return job
    
    def _backup_resources(self, job: BackupJob, namespace: str, output_dir: str) -> Dict[str, int]:
        """
        Backup resources of specified types in a namespace.
        
        Args:
            job: BackupJob specification
            namespace: Kubernetes namespace
            output_dir: Directory to save resource YAML files
            
        Returns:
            Dictionary with counts of backed up resources by type
        """
        backup_count = {}
        
        # Map of resource type to function that retrieves resources
        resource_functions = {
            "pods": lambda: self.core_v1.list_namespaced_pod(namespace),
            "services": lambda: self.core_v1.list_namespaced_service(namespace),
            "deployments": lambda: self.apps_v1.list_namespaced_deployment(namespace),
            "statefulsets": lambda: self.apps_v1.list_namespaced_stateful_set(namespace),
            "daemonsets": lambda: self.apps_v1.list_namespaced_daemon_set(namespace),
            "replicasets": lambda: self.apps_v1.list_namespaced_replica_set(namespace),
            "configmaps": lambda: self.core_v1.list_namespaced_config_map(namespace),
            "secrets": lambda: self.core_v1.list_namespaced_secret(namespace),
            "ingresses": lambda: self.networking_v1.list_namespaced_ingress(namespace),
            "jobs": lambda: self.batch_v1.list_namespaced_job(namespace),
            "cronjobs": lambda: self.batch_v1.list_namespaced_cron_job(namespace),
            "persistentvolumeclaims": lambda: self.core_v1.list_namespaced_persistent_volume_claim(namespace),
            "serviceaccounts": lambda: self.core_v1.list_namespaced_service_account(namespace),
            "roles": lambda: self.rbac_v1.list_namespaced_role(namespace),
            "rolebindings": lambda: self.rbac_v1.list_namespaced_role_binding(namespace)
        }
        
        # Process each resource type
        for resource_type in job.resource_types:
            if resource_type == "all":
                resource_types = list(resource_functions.keys())
            else:
                resource_types = [resource_type]
            
            for rt in resource_types:
                if rt not in resource_functions:
                    logger.warning(f"Unsupported resource type: {rt}")
                    continue
                
                try:
                    # Get resources of this type
                    resource_list = resource_functions[rt]()
                    
                    # Handle cases where items might be None
                    if not hasattr(resource_list, 'items') or resource_list.items is None:
                        logger.warning(f"No items found for resource type {rt} in namespace {namespace}")
                        continue
                    
                    # Filter by labels if specified
                    if job.include_labels:
                        resource_list = [r for r in resource_list.items if self._matches_labels(r, job.include_labels)]
                    else:
                        resource_list = resource_list.items
                    
                    if job.exclude_labels:
                        resource_list = [r for r in resource_list if not self._matches_labels(r, job.exclude_labels)]
                    
                    # Create directory for resource type
                    resource_dir = os.path.join(output_dir, rt)
                    os.makedirs(resource_dir, exist_ok=True)
                    
                    # Save each resource
                    count = 0
                    for resource in resource_list:
                        # Clean up resource for backup
                        resource_dict = self._clean_resource_for_backup(resource.to_dict())
                        
                        # Skip empty resources
                        if not resource_dict:
                            continue
                        
                        # Write resource to file
                        resource_name = resource.metadata.name
                        resource_file = os.path.join(resource_dir, f"{resource_name}.yaml")
                        
                        with open(resource_file, 'w') as f:
                            yaml.dump(resource_dict, f, default_flow_style=False)
                        
                        count += 1
                    
                    if count > 0:
                        backup_count[rt] = count
                
                except ApiException as e:
                    # Resource type might not exist in this namespace or cluster
                    logger.debug(f"Failed to backup {rt} in {namespace}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error backing up {rt} in {namespace}: {str(e)}")
        
        return backup_count
    
    def _clean_resource_for_backup(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean up a resource for backup by removing fields that are added by the system.
        
        Args:
            resource: Resource dictionary
            
        Returns:
            Cleaned resource dictionary
        """
        if not resource:
            return {}
        
        # Fields to remove from all resources
        remove_fields = [
            "status",
            "metadata.resourceVersion",
            "metadata.uid",
            "metadata.selfLink",
            "metadata.creationTimestamp",
            "metadata.generation",
            "metadata.managedFields"
        ]
        
        # Remove fields
        for field in remove_fields:
            parts = field.split(".")
            if len(parts) == 1:
                resource.pop(parts[0], None)
            elif len(parts) == 2 and parts[0] in resource and isinstance(resource[parts[0]], dict):
                resource[parts[0]].pop(parts[1], None)
        
        # Handle special cases
        if "metadata" in resource and "annotations" in resource["metadata"]:
            # Remove kubernetes.io annotations
            annotations = resource["metadata"]["annotations"]
            resource["metadata"]["annotations"] = {
                k: v for k, v in annotations.items()
                if not k.startswith("kubernetes.io/")
            }
        
        # For secrets, don't include token secrets
        if resource.get("kind") == "Secret" and resource.get("type") == "kubernetes.io/service-account-token":
            return {}  # Skip service account tokens
        
        return resource
    
    def _matches_labels(self, resource: Any, labels: Dict[str, str]) -> bool:
        """
        Check if a resource matches the given labels.
        
        Args:
            resource: Kubernetes resource
            labels: Labels to match
            
        Returns:
            True if the resource matches all labels, False otherwise
        """
        if not hasattr(resource, "metadata") or not resource.metadata.labels:
            return False
        
        resource_labels = resource.metadata.labels
        
        for key, value in labels.items():
            if key not in resource_labels or resource_labels[key] != value:
                return False
        
        return True
    
    def _enforce_backup_retention(self):
        """Enforce backup retention policy by deleting old backups."""
        backup_files = sorted([
            f for f in os.listdir(self.backup_dir)
            if f.endswith(".tar.gz")
        ], key=lambda x: os.path.getmtime(os.path.join(self.backup_dir, x)))
        
        # If we have more backups than the limit, delete the oldest ones
        if len(backup_files) > self.max_backups:
            for old_file in backup_files[:-self.max_backups]:
                try:
                    os.remove(os.path.join(self.backup_dir, old_file))
                    logger.info(f"Deleted old backup: {old_file}")
                except Exception as e:
                    logger.error(f"Failed to delete old backup {old_file}: {e}")
    
    def restore_from_backup(self, job: RestoreJob) -> RestoreJob:
        """
        Restore Kubernetes resources from a backup.
        
        Args:
            job: RestoreJob specification
            
        Returns:
            Updated RestoreJob with results
        """
        if self.use_mock:
            return self._create_mock_restore(job)
        
        logger.info(f"Starting restore job: {job.name} from backup {job.backup_id}")
        job.status = "running"
        self.restore_jobs.append(job)
        self._save_history()
        
        try:
            # Find the backup file
            backup_file = None
            for f in os.listdir(self.backup_dir):
                if f.startswith(f"{job.backup_id}_") and f.endswith(".tar.gz"):
                    backup_file = os.path.join(self.backup_dir, f)
                    break
            
            if not backup_file:
                raise FileNotFoundError(f"Backup with ID {job.backup_id} not found")
            
            # Create a temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract the backup
                with tarfile.open(backup_file, "r:gz") as tar:
                    tar.extractall(path=temp_dir)
                
                # Load metadata
                metadata_file = os.path.join(temp_dir, "metadata.json")
                if not os.path.exists(metadata_file):
                    raise FileNotFoundError("Metadata file not found in backup")
                
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Validate backup
                if metadata.get("backup_id") != job.backup_id:
                    logger.warning(f"Backup ID mismatch: expected {job.backup_id}, got {metadata.get('backup_id')}")
                
                # Determine namespaces to restore
                if "all" in job.namespaces:
                    namespaces = metadata.get("namespaces", [])
                    if "all" in namespaces:
                        namespaces = [d for d in os.listdir(temp_dir) 
                                     if os.path.isdir(os.path.join(temp_dir, d))
                                     and d != "metadata.json"]
                else:
                    namespaces = job.namespaces
                
                # Determine resource types to restore
                if not job.resource_types or "all" in job.resource_types:
                    resource_types = metadata.get("resource_types", [])
                    if "all" in resource_types:
                        # Get all resource types from the backup
                        resource_types = set()
                        for ns in namespaces:
                            ns_dir = os.path.join(temp_dir, ns)
                            if os.path.isdir(ns_dir):
                                resource_types.update([d for d in os.listdir(ns_dir) 
                                                     if os.path.isdir(os.path.join(ns_dir, d))])
                        resource_types = list(resource_types)
                else:
                    resource_types = job.resource_types
                
                # Process each namespace
                for namespace in namespaces:
                    # Ensure namespace exists
                    self._ensure_namespace_exists(namespace)
                    
                    # Process each resource type
                    for resource_type in resource_types:
                        resource_dir = os.path.join(temp_dir, namespace, resource_type)
                        if not os.path.isdir(resource_dir):
                            continue
                        
                        # Process each resource file
                        for resource_file in os.listdir(resource_dir):
                            if not resource_file.endswith(".yaml"):
                                continue
                            
                            resource_path = os.path.join(resource_dir, resource_file)
                            
                            # Restore the resource
                            restored = self._restore_resource(namespace, resource_type, resource_path, 
                                                          job.restore_strategy, job.include_labels, job.exclude_labels)
                            
                            if restored:
                                # Update job statistics
                                if resource_type not in job.resources_restored:
                                    job.resources_restored[resource_type] = 0
                                job.resources_restored[resource_type] += 1
                
                # Update job status
                total_restored = sum(job.resources_restored.values())
                if total_restored == 0:
                    logger.warning(f"No resources were restored for job: {job.name}")
                
                job.status = "completed"
                logger.info(f"Restore job completed: {job.name}, restored {total_restored} resources")
        
        except Exception as e:
            logger.error(f"Error during restore job {job.name}: {e}")
            job.status = "failed"
            job.error_message = str(e)
        
        # Save updated history
        self._save_history()
        
        return job
    
    def _ensure_namespace_exists(self, namespace: str):
        """
        Ensure that a namespace exists, creating it if necessary.
        
        Args:
            namespace: Namespace name
        """
        if namespace == "default":
            return
        
        try:
            self.core_v1.read_namespace(namespace)
        except ApiException as e:
            if e.status == 404:
                # Namespace doesn't exist, create it
                body = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))
                self.core_v1.create_namespace(body=body)
                logger.info(f"Created namespace: {namespace}")
            else:
                raise
    
    def _restore_resource(self, namespace: str, resource_type: str, resource_file: str, 
                        strategy: str, include_labels: Dict[str, str], exclude_labels: Dict[str, str]) -> bool:
        """
        Restore a single resource from a file.
        
        Args:
            namespace: Namespace for the resource
            resource_type: Type of resource
            resource_file: Path to the resource YAML file
            strategy: Restore strategy ("create_or_replace", "create_only", "replace_only")
            include_labels: Labels that resources must have to be restored
            exclude_labels: Labels that resources must not have to be restored
            
        Returns:
            True if the resource was restored, False otherwise
        """
        try:
            # Load resource from file
            with open(resource_file, 'r') as f:
                resource = yaml.safe_load(f)
            
            # Skip if resource is empty
            if not resource:
                return False
            
            # Check labels if specified
            if include_labels and "metadata" in resource and "labels" in resource["metadata"]:
                resource_labels = resource["metadata"]["labels"]
                if not all(key in resource_labels and resource_labels[key] == value 
                          for key, value in include_labels.items()):
                    return False
            
            if exclude_labels and "metadata" in resource and "labels" in resource["metadata"]:
                resource_labels = resource["metadata"]["labels"]
                if any(key in resource_labels and resource_labels[key] == value 
                      for key, value in exclude_labels.items()):
                    return False
            
            # Set namespace in resource metadata
            if "metadata" in resource:
                resource["metadata"]["namespace"] = namespace
            
            # Create the resource in Kubernetes
            return self._apply_resource(namespace, resource_type, resource, strategy)
        
        except Exception as e:
            resource_name = os.path.basename(resource_file).replace(".yaml", "")
            logger.error(f"Failed to restore {resource_type}/{resource_name} in {namespace}: {e}")
            return False
    
    def _apply_resource(self, namespace: str, resource_type: str, resource: Dict[str, Any], strategy: str) -> bool:
        """
        Apply a resource to the Kubernetes cluster.
        
        Args:
            namespace: Namespace for the resource
            resource_type: Type of resource
            resource: Resource definition
            strategy: Restore strategy
            
        Returns:
            True if the resource was applied, False otherwise
        """
        # Map of resource type to API function
        api_functions = {
            "pods": (self.core_v1.create_namespaced_pod, self.core_v1.replace_namespaced_pod, self.core_v1.read_namespaced_pod),
            "services": (self.core_v1.create_namespaced_service, self.core_v1.replace_namespaced_service, self.core_v1.read_namespaced_service),
            "deployments": (self.apps_v1.create_namespaced_deployment, self.apps_v1.replace_namespaced_deployment, self.apps_v1.read_namespaced_deployment),
            "statefulsets": (self.apps_v1.create_namespaced_stateful_set, self.apps_v1.replace_namespaced_stateful_set, self.apps_v1.read_namespaced_stateful_set),
            "daemonsets": (self.apps_v1.create_namespaced_daemon_set, self.apps_v1.replace_namespaced_daemon_set, self.apps_v1.read_namespaced_daemon_set),
            "replicasets": (self.apps_v1.create_namespaced_replica_set, self.apps_v1.replace_namespaced_replica_set, self.apps_v1.read_namespaced_replica_set),
            "configmaps": (self.core_v1.create_namespaced_config_map, self.core_v1.replace_namespaced_config_map, self.core_v1.read_namespaced_config_map),
            "secrets": (self.core_v1.create_namespaced_secret, self.core_v1.replace_namespaced_secret, self.core_v1.read_namespaced_secret),
            "ingresses": (self.networking_v1.create_namespaced_ingress, self.networking_v1.replace_namespaced_ingress, self.networking_v1.read_namespaced_ingress),
            "jobs": (self.batch_v1.create_namespaced_job, self.batch_v1.replace_namespaced_job, self.batch_v1.read_namespaced_job),
            "cronjobs": (self.batch_v1.create_namespaced_cron_job, self.batch_v1.replace_namespaced_cron_job, self.batch_v1.read_namespaced_cron_job),
            "persistentvolumeclaims": (self.core_v1.create_namespaced_persistent_volume_claim, self.core_v1.replace_namespaced_persistent_volume_claim, self.core_v1.read_namespaced_persistent_volume_claim),
            "serviceaccounts": (self.core_v1.create_namespaced_service_account, self.core_v1.replace_namespaced_service_account, self.core_v1.read_namespaced_service_account),
            "roles": (self.rbac_v1.create_namespaced_role, self.rbac_v1.replace_namespaced_role, self.rbac_v1.read_namespaced_role),
            "rolebindings": (self.rbac_v1.create_namespaced_role_binding, self.rbac_v1.replace_namespaced_role_binding, self.rbac_v1.read_namespaced_role_binding)
        }
        
        if resource_type not in api_functions:
            logger.warning(f"Unsupported resource type: {resource_type}")
            return False
        
        create_func, replace_func, read_func = api_functions[resource_type]
        resource_name = resource["metadata"]["name"]
        
        try:
            # Check if resource exists
            exists = True
            try:
                read_func(name=resource_name, namespace=namespace)
            except ApiException as e:
                if e.status == 404:
                    exists = False
                else:
                    raise
            
            # Apply based on strategy
            if strategy == "create_only" and exists:
                logger.info(f"Skipping {resource_type}/{resource_name} in {namespace}: already exists")
                return False
            
            if strategy == "replace_only" and not exists:
                logger.info(f"Skipping {resource_type}/{resource_name} in {namespace}: does not exist")
                return False
            
            if exists:
                if strategy in ["create_or_replace", "replace_only"]:
                    replace_func(name=resource_name, namespace=namespace, body=resource)
                    logger.info(f"Replaced {resource_type}/{resource_name} in {namespace}")
                    return True
            else:
                if strategy in ["create_or_replace", "create_only"]:
                    create_func(namespace=namespace, body=resource)
                    logger.info(f"Created {resource_type}/{resource_name} in {namespace}")
                    return True
        
        except ApiException as e:
            logger.error(f"API error applying {resource_type}/{resource_name} in {namespace}: {e}")
            return False
        
        return False
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all backup jobs.
        
        Returns:
            List of backup job dictionaries
        """
        return [job.to_dict() for job in self.backup_jobs]
    
    def get_restore_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all restore jobs.
        
        Returns:
            List of restore job dictionaries
        """
        return [job.to_dict() for job in self.restore_jobs]
    
    def get_backup_job(self, backup_id: str) -> Optional[BackupJob]:
        """
        Get a specific backup job by ID.
        
        Args:
            backup_id: Backup job ID
            
        Returns:
            BackupJob if found, None otherwise
        """
        for job in self.backup_jobs:
            if job.id == backup_id:
                return job
        return None
    
    def get_backup_file_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a backup file.
        
        Args:
            backup_id: Backup job ID
            
        Returns:
            Dictionary with file information if found, None otherwise
        """
        for f in os.listdir(self.backup_dir):
            if f.startswith(f"{backup_id}_") and f.endswith(".tar.gz"):
                file_path = os.path.join(self.backup_dir, f)
                return {
                    "filename": f,
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "created": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                }
        return None
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup and its associated file.
        
        Args:
            backup_id: Backup job ID
            
        Returns:
            True if the backup was deleted, False otherwise
        """
        # Delete the backup file
        file_info = self.get_backup_file_info(backup_id)
        if file_info:
            try:
                os.remove(file_info["path"])
                logger.info(f"Deleted backup file: {file_info['filename']}")
            except Exception as e:
                logger.error(f"Failed to delete backup file {file_info['filename']}: {e}")
                return False
        
        # Remove from job history
        self.backup_jobs = [job for job in self.backup_jobs if job.id != backup_id]
        self._save_history()
        
        return True

    def _generate_mock_backup_data(self):
        """Generate mock backup data for testing."""
        import random
        import uuid
        
        logger.info("Generating mock backup data")
        
        # Generate sample backup jobs
        namespaces = ["default", "kube-system", "application", "monitoring"]
        resource_types = ["deployments", "services", "configmaps", "secrets"]
        
        # Create 3-5 mock backups
        for i in range(random.randint(3, 5)):
            backup_id = str(uuid.uuid4())
            
            # Create a backup from a few days/hours ago
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            timestamp = (datetime.now() - 
                        (days_ago * timedelta(days=1)) - 
                        (hours_ago * timedelta(hours=1))).isoformat()
            
            # Random selection of namespaces and resource types
            selected_namespaces = random.sample(namespaces, 
                                              k=random.randint(1, len(namespaces)))
            selected_resources = random.sample(resource_types, 
                                             k=random.randint(1, len(resource_types)))
            
            # Create the backup job
            backup_job = BackupJob(
                id=backup_id,
                name=f"mock-backup-{i+1}",
                namespaces=selected_namespaces,
                resource_types=selected_resources,
                timestamp=timestamp,
                status="completed"
            )
            
            # Add random resource counts
            resources_backed_up = {}
            for resource_type in selected_resources:
                resources_backed_up[resource_type] = random.randint(1, 15)
            backup_job.resources_backed_up = resources_backed_up
            
            # Add random file size (1-100 MB)
            backup_job.file_size = random.randint(1, 100) * 1024 * 1024
            
            self.backup_jobs.append(backup_job)
        
        # Create 1-3 mock restore jobs
        for i in range(random.randint(1, 3)):
            # Pick a random backup to restore from
            if self.backup_jobs:
                source_backup = random.choice(self.backup_jobs)
                
                restore_id = str(uuid.uuid4())
                # Create a restore from a few hours ago
                hours_ago = random.randint(0, 12)
                timestamp = (datetime.now() - 
                            (hours_ago * timedelta(hours=1))).isoformat()
                
                # Create the restore job
                restore_job = RestoreJob(
                    id=restore_id,
                    backup_id=source_backup.id,
                    name=f"mock-restore-{i+1}",
                    namespaces=source_backup.namespaces,
                    resource_types=source_backup.resource_types,
                    timestamp=timestamp,
                    status="completed"
                )
                
                # Add random resource counts (subset of backup)
                resources_restored = {}
                for resource_type, count in source_backup.resources_backed_up.items():
                    resources_restored[resource_type] = random.randint(1, count)
                restore_job.resources_restored = resources_restored
                
                self.restore_jobs.append(restore_job)
        
        # Save the mock history
        self._save_history()

    def _create_mock_backup(self, job: BackupJob) -> BackupJob:
        """Create a mock backup for testing."""
        import random
        import time
        
        logger.info(f"Creating mock backup: {job.name}")
        
        # Simulate a backup process
        job.status = "running"
        
        # Simulate work
        time.sleep(0.5)
        
        # Generate random resource counts
        resources_backed_up = {}
        for resource_type in job.resource_types:
            # If "all" is specified, use some common resource types
            if resource_type == "all":
                common_types = ["deployments", "services", "pods", "configmaps", "secrets"]
                for common_type in common_types:
                    resources_backed_up[common_type] = random.randint(1, 15)
            else:
                resources_backed_up[resource_type] = random.randint(1, 15)
        
        job.resources_backed_up = resources_backed_up
        
        # Add random file size (1-100 MB)
        job.file_size = random.randint(1, 100) * 1024 * 1024
        
        # Mark as completed
        job.status = "completed"
        
        # Add to history
        self.backup_jobs.append(job)
        self._save_history()
        
        return job

    def _create_mock_restore(self, job: RestoreJob) -> RestoreJob:
        """Create a mock restore for testing."""
        import random
        import time
        
        logger.info(f"Creating mock restore: {job.name}")
        
        # First, find the referenced backup
        source_backup = None
        for backup in self.backup_jobs:
            if backup.id == job.backup_id:
                source_backup = backup
                break
        
        if not source_backup:
            job.status = "failed"
            job.error_message = f"Backup with ID {job.backup_id} not found"
            return job
        
        # Simulate a restore process
        job.status = "running"
        
        # Simulate work
        time.sleep(0.5)
        
        # Generate random resource counts (subset of backup)
        resources_restored = {}
        for resource_type, count in source_backup.resources_backed_up.items():
            # If resource types filter is specified, only include those
            if job.resource_types and resource_type not in job.resource_types and "all" not in job.resource_types:
                continue
            
            resources_restored[resource_type] = random.randint(1, count)
        
        job.resources_restored = resources_restored
        
        # Mark as completed
        job.status = "completed"
        
        # Add to history
        self.restore_jobs.append(job)
        self._save_history()
        
        return job 