"""
Command-line interface for the Kubernetes prediction service.
"""
import os
import sys
import logging
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler

from kagent.services.k8s_prediction_service import KubernetesPredictionService

# Configure logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("kagent")

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """KAgent: AI-powered Kubernetes Assistant"""
    pass

@cli.command()
@click.option("--metrics-interval", default=60, help="Metrics collection interval in seconds")
@click.option("--prediction-interval", default=300, help="Prediction interval in seconds")
@click.option("--auto-remediate", is_flag=True, help="Enable automatic remediation")
@click.option("--kubeconfig", help="Path to kubeconfig file")
@click.option("--history-file", default="~/.kagent/history.json", help="Path to history file")
@click.option("--run-once", is_flag=True, help="Run prediction once and exit")
def predict(
    metrics_interval: int,
    prediction_interval: int,
    auto_remediate: bool,
    kubeconfig: Optional[str],
    history_file: str,
    run_once: bool
):
    """Start the Kubernetes prediction service"""
    # Expand home directory if needed
    history_file = os.path.expanduser(history_file)
    
    console.print("[bold green]Starting Kubernetes prediction service[/bold green]")
    console.print(f"  Metrics interval: {metrics_interval} seconds")
    console.print(f"  Prediction interval: {prediction_interval} seconds")
    console.print(f"  Auto-remediation: {'Enabled' if auto_remediate else 'Disabled'}")
    
    try:
        service = KubernetesPredictionService(
            metrics_interval=metrics_interval,
            prediction_interval=prediction_interval,
            auto_remediate=auto_remediate,
            kubeconfig_path=kubeconfig,
            history_file=history_file
        )
        
        if run_once:
            # Run a single prediction
            console.print("[bold]Running single prediction...[/bold]")
            result = service.run_manual_prediction()
            
            # Print results
            console.print("\n[bold]Prediction Results:[/bold]")
            if "error" in result:
                console.print(f"[bold red]Error:[/bold red] {result['error']}")
            else:
                console.print(f"Found [bold]{len(result['issues'])}[/bold] issues")
                for issue in result['issues']:
                    severity_color = "red" if issue['severity'] == "critical" else "yellow"
                    console.print(f"  [[{severity_color}]{issue['severity']}[/{severity_color}]] {issue['issue_type']} on {issue['component']}")
                    console.print(f"    Impact: {issue['impact']}")
                
                if result['remediation_suggestions']:
                    console.print("\n[bold]Remediation Suggestions:[/bold]")
                    for suggestion in result['remediation_suggestions']:
                        console.print(f"  For {suggestion['issue_type']} on {suggestion['component']}:")
                        for action in suggestion['actions']:
                            console.print(f"    - {action}")
        else:
            # Start the continuous service
            service.start()
            console.print("[bold]Service started, press Ctrl+C to stop[/bold]")
            
            try:
                # Keep the main thread alive
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[bold]Stopping service...[/bold]")
                service.stop()
                console.print("[bold green]Service stopped[/bold green]")
    
    except Exception as e:
        logger.error(f"Error starting prediction service: {e}")
        sys.exit(1)

@cli.command()
@click.option("--kubeconfig", help="Path to kubeconfig file")
def status(kubeconfig: Optional[str]):
    """Show current Kubernetes cluster status"""
    console.print("[bold]Checking Kubernetes cluster status...[/bold]")
    
    try:
        service = KubernetesPredictionService(
            kubeconfig_path=kubeconfig,
            history_file=os.path.expanduser("~/.kagent/history.json")
        )
        
        # Run a manual prediction
        result = service.run_manual_prediction()
        
        # Display cluster status
        status = "Error"
        message = "Unknown"
        status_color = "red"
        
        if "error" in result:
            status = "Error"
            message = result["error"]
            status_color = "red"
        else:
            # Determine status based on issues
            critical_issues = [i for i in result["issues"] if i["severity"] == "critical"]
            warning_issues = [i for i in result["issues"] if i["severity"] == "warning"]
            
            if critical_issues:
                status = "Critical"
                message = f"{len(critical_issues)} critical issues found"
                status_color = "red"
            elif warning_issues:
                status = "Warning"
                message = f"{len(warning_issues)} warning issues found"
                status_color = "yellow"
            else:
                status = "Healthy"
                message = "No issues detected"
                status_color = "green"
        
        # Display results
        console.print(f"\nCluster Status: [bold {status_color}]{status}[/bold {status_color}]")
        console.print(f"Message: {message}")
        
        if "issues" in result and result["issues"]:
            console.print("\n[bold]Issues:[/bold]")
            for issue in result["issues"]:
                severity_color = "red" if issue['severity'] == "critical" else "yellow"
                console.print(f"  [[{severity_color}]{issue['severity']}[/{severity_color}]] {issue['issue_type']} on {issue['component']}")
                console.print(f"    Impact: {issue['impact']}")
        
        if "remediation_suggestions" in result and result["remediation_suggestions"]:
            console.print("\n[bold]Remediation Suggestions:[/bold]")
            for suggestion in result["remediation_suggestions"]:
                console.print(f"  For {suggestion['issue_type']} on {suggestion['component']}:")
                for action in suggestion["actions"]:
                    console.print(f"    - {action}")
    
    except Exception as e:
        logger.error(f"Error checking cluster status: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cli() 