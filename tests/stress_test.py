#!/usr/bin/env python3
"""
Script to simulate load on the test cluster and collect metrics
"""

import os
import time
import subprocess
import json
import random
from datetime import datetime

def run_command(cmd):
    """Run a shell command and return the output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def generate_load():
    """Generate load on the test pods"""
    # Get the pod names
    print("Getting pod names...")
    pod_names = run_command("kubectl get pods -l app=nginx-test -o jsonpath='{.items[*].metadata.name}'").split()
    
    if not pod_names:
        print("No pods found. Make sure the nginx-test deployment is running.")
        return
    
    print(f"Found {len(pod_names)} pods: {', '.join(pod_names)}")
    
    # Choose a random pod to generate load on
    target_pod = random.choice(pod_names)
    print(f"Generating load on pod: {target_pod}")
    
    # Create a loop that generates HTTP requests to the pod
    for _ in range(100):
        run_command(f"kubectl exec {target_pod} -- sh -c 'dd if=/dev/zero of=/tmp/dummy bs=1M count=10'")
        time.sleep(0.1)
    
    print("Load generation completed")

def collect_metrics():
    """Collect metrics from the cluster"""
    print("\nCollecting cluster metrics...")
    
    # Get node metrics
    nodes = json.loads(run_command("kubectl get nodes -o json"))
    
    for node in nodes.get("items", []):
        node_name = node["metadata"]["name"]
        print(f"\nNode: {node_name}")
        
        # Get node conditions
        conditions = node.get("status", {}).get("conditions", [])
        for condition in conditions:
            if condition["type"] in ["Ready", "DiskPressure", "MemoryPressure", "PIDPressure"]:
                status = condition["status"] == "True"
                print(f"  {condition['type']}: {status}")
    
    # Get pod metrics
    pods = json.loads(run_command("kubectl get pods -o json"))
    
    for pod in pods.get("items", []):
        pod_name = pod["metadata"]["name"]
        pod_status = pod["status"]["phase"]
        restarts = 0
        
        # Count container restarts
        for container_status in pod["status"].get("containerStatuses", []):
            restarts += container_status.get("restartCount", 0)
        
        print(f"\nPod: {pod_name}")
        print(f"  Status: {pod_status}")
        print(f"  Restarts: {restarts}")

def main():
    """Main function"""
    print(f"=== Stress Test Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    try:
        # First collect baseline metrics
        print("Collecting baseline metrics...")
        collect_metrics()
        
        # Generate load
        generate_load()
        
        # Collect metrics after load
        print("\nCollecting metrics after load...")
        collect_metrics()
        
    except Exception as e:
        print(f"Error: {e}")
    
    print(f"\n=== Stress Test Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

if __name__ == "__main__":
    main() 