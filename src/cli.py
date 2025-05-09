import typer
from autogen_core import CancellationToken
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
import logging
import os
import sys
from rich.console import Console
from rich.logging import RichHandler

from kagent.tools.argo._argo_rollouts_k8sgw_installation import (
    check_plugin_logs,
    verify_gateway_plugin,
)
from kagent.tools.argo._kubectl_argo_rollouts import (
    pause_rollout,
    promote_rollout,
    set_rollout_image,
    verify_argo_rollouts_controller_install,
    verify_kubectl_plugin_install,
)
from kagent.tools.helm._helm import (
    helm_get_release,
    helm_list_releases,
    helm_repo_add,
    helm_repo_update,
    helm_uninstall,
    upgrade_release,
)
from kagent.tools.istio._istioctl import (
    analyze_cluster_configuration,
    apply_waypoint,
    delete_waypoint,
    generate_manifest,
    generate_waypoint,
    install_istio,
    list_waypoints,
    proxy_config,
    proxy_status,
    remote_clusters,
    ztunnel_config,
)
from kagent.tools.k8s._kubectl import (
    annotate_resource,
    apply_manifest,
    check_service_connectivity,
    create_resource,
    delete_resource,
    describe_resource,
    get_available_api_resources,
    get_cluster_configuration,
    get_events,
    get_pod_logs,
    get_resource_yaml,
    get_resources,
    label_resource,
    patch_resource,
    remove_annotation,
    remove_label,
    rollout,
    scale,
)
from kagent.tools.prometheus._prometheus import (
    AlertmanagersInput,
    AlertmanagersTool,
    AlertsInput,
    AlertsTool,
    BaseTool,
    BuildInfoInput,
    BuildInfoTool,
    Config,
    LabelNamesInput,
    LabelNamesTool,
    LabelValuesInput,
    LabelValuesTool,
    MetadataInput,
    MetadataTool,
    QueryInput,
    QueryRangeInput,
    QueryRangeTool,
    QueryTool,
    RulesInput,
    RulesTool,
    RuntimeInfoInput,
    RuntimeInfoTool,
    SeriesInput,
    SeriesQueryTool,
    StatusConfigInput,
    StatusConfigTool,
    StatusFlagsInput,
    StatusFlagsTool,
    TargetMetadataInput,
    TargetMetadataTool,
    TargetsInput,
    TargetsTool,
    TSDBStatusInput,
    TSDBStatusTool,
)

from kagent.services.k8s_prediction_service import KubernetesPredictionService
from kagent.agents.security_scanner import KubernetesSecurityScanner
from kagent.agents.cost_optimizer import KubernetesCostOptimizer
from kagent.agents.backup_manager import KubernetesBackupManager, BackupJob, RestoreJob
from kagent.tools.utils.train_model import train_and_save_model

import uuid

# Configure rich logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("kagent")

app = typer.Typer()

mcp = FastMCP("My App")


def add_typed_tool(cfg_type: type[BaseModel], tool: BaseTool):
    def query_tool(cfg: cfg_type):
        return tool.run_json(cfg.model_dump(), CancellationToken())

    mcp.add_tool(
        query_tool,
        tool.name,
        tool.description,
    )


@app.command()
def prometheus(
    url: str = typer.Option(..., "--url", "-u"),
):
    cfg = Config(base_url=url)

    def query_tool(input: QueryInput):
        return QueryTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(query_tool, QueryTool(cfg).name, QueryTool(cfg).description)

    def query_range_tool(input: QueryRangeInput):
        return QueryRangeTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(query_range_tool, QueryRangeTool(cfg).name, QueryRangeTool(cfg).description)

    def series_query_tool(input: SeriesInput):
        return SeriesQueryTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(series_query_tool, SeriesQueryTool(cfg).name, SeriesQueryTool(cfg).description)

    def label_names_tool(input: LabelNamesInput):
        return LabelNamesTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(label_names_tool, LabelNamesTool(cfg).name, LabelNamesTool(cfg).description)

    def label_values_tool(input: LabelValuesInput):
        return LabelValuesTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(label_values_tool, LabelValuesTool(cfg).name, LabelValuesTool(cfg).description)

    def alertmanagers_tool(input: AlertmanagersInput):
        return AlertmanagersTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(alertmanagers_tool, AlertmanagersTool(cfg).name, AlertmanagersTool(cfg).description)

    def target_metadata_tool(input: TargetMetadataInput):
        return TargetMetadataTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(target_metadata_tool, TargetMetadataTool(cfg).name, TargetMetadataTool(cfg).description)

    def status_config_tool(input: StatusConfigInput):
        return StatusConfigTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(status_config_tool, StatusConfigTool(cfg).name, StatusConfigTool(cfg).description)

    def status_flags_tool(input: StatusFlagsInput):
        return StatusFlagsTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(status_flags_tool, StatusFlagsTool(cfg).name, StatusFlagsTool(cfg).description)

    def runtime_info_tool(input: RuntimeInfoInput):
        return RuntimeInfoTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(runtime_info_tool, RuntimeInfoTool(cfg).name, RuntimeInfoTool(cfg).description)

    def build_info_tool(input: BuildInfoInput):
        return BuildInfoTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(build_info_tool, BuildInfoTool(cfg).name, BuildInfoTool(cfg).description)

    def tsdb_status_tool(input: TSDBStatusInput):
        return TSDBStatusTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(tsdb_status_tool, TSDBStatusTool(cfg).name, TSDBStatusTool(cfg).description)

    def metadata_tool(input: MetadataInput):
        return MetadataTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(metadata_tool, MetadataTool(cfg).name, MetadataTool(cfg).description)

    def alerts_tool(input: AlertsInput):
        return AlertsTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(alerts_tool, AlertsTool(cfg).name, AlertsTool(cfg).description)

    def rules_tool(input: RulesInput):
        return RulesTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(rules_tool, RulesTool(cfg).name, RulesTool(cfg).description)

    def targets_tool(input: TargetsInput):
        return TargetsTool(cfg).run_json(input.model_dump(), CancellationToken())

    mcp.add_tool(targets_tool, TargetsTool(cfg).name, TargetsTool(cfg).description)

    mcp.run()


@app.command()
def argo():
    mcp.add_tool(verify_gateway_plugin._func, verify_gateway_plugin.name, verify_gateway_plugin.description)
    mcp.add_tool(check_plugin_logs._func, check_plugin_logs.name, check_plugin_logs.description)
    mcp.add_tool(
        verify_kubectl_plugin_install._func,
        verify_kubectl_plugin_install.name,
        verify_kubectl_plugin_install.description,
    )
    mcp.add_tool(
        verify_argo_rollouts_controller_install._func,
        verify_argo_rollouts_controller_install.name,
        verify_argo_rollouts_controller_install.description,
    )
    mcp.add_tool(pause_rollout._func, pause_rollout.name, pause_rollout.description)
    mcp.add_tool(promote_rollout._func, promote_rollout.name, promote_rollout.description)
    mcp.add_tool(set_rollout_image._func, set_rollout_image.name, set_rollout_image.description)

    mcp.run()


@app.command()
def istio():
    mcp.add_tool(
        analyze_cluster_configuration._func,
        analyze_cluster_configuration.name,
        analyze_cluster_configuration.description,
    )
    mcp.add_tool(apply_waypoint._func, apply_waypoint.name, apply_waypoint.description)
    mcp.add_tool(delete_waypoint._func, delete_waypoint.name, delete_waypoint.description)
    mcp.add_tool(list_waypoints._func, list_waypoints.name, list_waypoints.description)
    mcp.add_tool(generate_manifest._func, generate_manifest.name, generate_manifest.description)
    mcp.add_tool(generate_waypoint._func, generate_waypoint.name, generate_waypoint.description)
    mcp.add_tool(install_istio._func, install_istio.name, install_istio.description)
    mcp.add_tool(proxy_config._func, proxy_config.name, proxy_config.description)
    mcp.add_tool(proxy_status._func, proxy_status.name, proxy_status.description)
    mcp.add_tool(remote_clusters._func, remote_clusters.name, remote_clusters.description)
    mcp.add_tool(ztunnel_config._func, ztunnel_config.name, ztunnel_config.description)
    mcp.add_tool(proxy_status._func, proxy_status.name, proxy_status.description)
    mcp.add_tool(remote_clusters._func, remote_clusters.name, remote_clusters.description)

    mcp.run()


@app.command()
def k8s():
    mcp.add_tool(apply_manifest._func, apply_manifest.name, apply_manifest.description)
    mcp.add_tool(get_pod_logs._func, get_pod_logs.name, get_pod_logs.description)
    mcp.add_tool(get_resources._func, get_resources.name, get_resources.description)
    mcp.add_tool(get_resource_yaml._func, get_resource_yaml.name, get_resource_yaml.description)
    mcp.add_tool(get_cluster_configuration._func, get_cluster_configuration.name, get_cluster_configuration.description)
    mcp.add_tool(describe_resource._func, describe_resource.name, describe_resource.description)
    mcp.add_tool(delete_resource._func, delete_resource.name, delete_resource.description)
    mcp.add_tool(label_resource._func, label_resource.name, label_resource.description)
    mcp.add_tool(annotate_resource._func, annotate_resource.name, annotate_resource.description)
    mcp.add_tool(remove_label._func, remove_label.name, remove_label.description)
    mcp.add_tool(remove_annotation._func, remove_annotation.name, remove_annotation.description)
    mcp.add_tool(rollout._func, rollout.name, rollout.description)
    mcp.add_tool(scale._func, scale.name, scale.description)
    mcp.add_tool(patch_resource._func, patch_resource.name, patch_resource.description)
    mcp.add_tool(
        check_service_connectivity._func, check_service_connectivity.name, check_service_connectivity.description
    )
    mcp.add_tool(create_resource._func, create_resource.name, create_resource.description)
    mcp.add_tool(get_events._func, get_events.name, get_events.description)
    mcp.add_tool(
        get_available_api_resources._func, get_available_api_resources.name, get_available_api_resources.description
    )
    mcp.run()


@app.command()
def helm():
    mcp.add_tool(helm_list_releases._func, helm_list_releases.name, helm_list_releases.description)
    mcp.add_tool(helm_get_release._func, helm_get_release.name, helm_get_release.description)
    mcp.add_tool(helm_uninstall._func, helm_uninstall.name, helm_uninstall.description)
    mcp.add_tool(upgrade_release._func, upgrade_release.name, upgrade_release.description)
    mcp.add_tool(helm_repo_add._func, helm_repo_add.name, helm_repo_add.description)
    mcp.add_tool(helm_repo_update._func, helm_repo_update.name, helm_repo_update.description)
    mcp.run()


@app.command()
def serve(
    host: str = "127.0.0.1",
    port: int = 8081,
):
    import logging
    import os

    from autogenstudio.cli import ui
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.openai import OpenAIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    logging.basicConfig(level=logging.INFO)
    tracing_enabled = os.getenv("OTEL_TRACING_ENABLED", "false").lower() == "true"
    if tracing_enabled:
        logging.info("Enabling tracing")
        tracer_provider = TracerProvider(resource=Resource({"service.name": "kagent"}))
        processor = BatchSpanProcessor(OTLPSpanExporter())
        tracer_provider.add_span_processor(processor)
        trace.set_tracer_provider(tracer_provider)
        HTTPXClientInstrumentor().instrument()
        OpenAIInstrumentor().instrument()

    ui(host=host, port=port)


@app.command()
def ui(
    host: str = "127.0.0.1",
    port: int = 8080,
    reload: bool = False,
    log_level: str = "info",
):
    """Launch the Kagent UI with Ollama integration."""
    from kagent.ui import serve_ui
    
    serve_ui(host=host, port=port, reload=reload, log_level=log_level)


@app.command()
def predict(
    metrics_interval: int = typer.Option(60, help="Metrics collection interval in seconds"),
    prediction_interval: int = typer.Option(300, help="Prediction interval in seconds"),
    auto_remediate: bool = typer.Option(False, help="Enable automatic remediation"),
    kubeconfig: str = typer.Option(None, help="Path to kubeconfig file"),
    history_file: str = typer.Option("~/.kagent/history.json", help="Path to history file"),
    run_once: bool = typer.Option(False, help="Run prediction once and exit"),
    use_mock: bool = typer.Option(False, help="Use mock data instead of real Kubernetes cluster"),
):
    """Start the Kubernetes prediction service."""
    # Expand home directory if needed
    history_file = os.path.expanduser(history_file)
    
    console.print("[bold green]Starting Kubernetes prediction service[/bold green]")
    console.print(f"  Metrics interval: {metrics_interval} seconds")
    console.print(f"  Prediction interval: {prediction_interval} seconds")
    console.print(f"  Auto-remediation: {'Enabled' if auto_remediate else 'Disabled'}")
    console.print(f"  Mock mode: {'Enabled' if use_mock else 'Disabled'}")
    
    try:
        service = KubernetesPredictionService(
            metrics_interval=metrics_interval,
            prediction_interval=prediction_interval,
            auto_remediate=auto_remediate,
            kubeconfig_path=kubeconfig,
            history_file=history_file,
            use_mock=use_mock
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

@app.command()
def k8s_status(
    kubeconfig: str = typer.Option(None, help="Path to kubeconfig file"),
):
    """Show current Kubernetes cluster status."""
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

@app.command()
def security_scan(
    kubeconfig: str = typer.Option(None, help="Path to kubeconfig file"),
    output_format: str = typer.Option("table", help="Output format: table, json"),
    history_file: str = typer.Option("~/.kagent/security_history.json", help="Path to store scan history"),
):
    """Run a security scan on the Kubernetes cluster"""
    logger.info("Starting security scan")
    
    try:
        # Initialize scanner
        scanner = KubernetesSecurityScanner(
            kubeconfig_path=kubeconfig,
            history_file=os.path.expanduser(history_file)
        )
        
        # Run scan
        scan_result = scanner.perform_security_scan()
        
        # Display results
        vulnerabilities = scan_result.vulnerabilities
        misconfigurations = scan_result.misconfigurations
        compliance_issues = scan_result.compliance_issues
        
        total_issues = len(vulnerabilities) + len(misconfigurations) + len(compliance_issues)
        
        if output_format == "json":
            import json
            print(json.dumps(scan_result.to_dict(), indent=2))
        else:
            console.print(f"\n[bold]Security Scan Results:[/bold]")
            console.print(f"Found [bold]{total_issues}[/bold] security issues")
            
            if vulnerabilities:
                console.print("\n[bold red]Vulnerabilities:[/bold red]")
                for vuln in vulnerabilities:
                    console.print(f"  [[{vuln['severity']}]] {vuln['type']} in {vuln['resource_type']}/{vuln['namespace']}/{vuln['name']}")
                    console.print(f"    Description: {vuln['description']}")
                    console.print(f"    Remediation: {vuln['remediation']}")
            
            if misconfigurations:
                console.print("\n[bold yellow]Misconfigurations:[/bold yellow]")
                for misconfig in misconfigurations:
                    console.print(f"  [[{misconfig['severity']}]] {misconfig['type']} in {misconfig['resource_type']}/{misconfig['namespace']}/{misconfig['name']}")
                    console.print(f"    Description: {misconfig['description']}")
                    console.print(f"    Remediation: {misconfig['remediation']}")
            
            if compliance_issues:
                console.print("\n[bold blue]Compliance Issues:[/bold blue]")
                for issue in compliance_issues:
                    console.print(f"  [[{issue['severity']}]] {issue['type']} in {issue['resource_type']}/{issue.get('namespace', 'N/A')}/{issue['name']}")
                    console.print(f"    Description: {issue['description']}")
                    console.print(f"    Remediation: {issue['remediation']}")
    
    except Exception as e:
        logger.error(f"Error performing security scan: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

@app.command()
def optimize_costs(
    kubeconfig: str = typer.Option(None, help="Path to kubeconfig file"),
    output_format: str = typer.Option("table", help="Output format: table, json"),
    history_file: str = typer.Option("~/.kagent/cost_history.json", help="Path to store optimization history"),
    cloud_provider: str = typer.Option("aws", help="Cloud provider (aws, gcp, azure)"),
):
    """Analyze cluster resources for cost optimization opportunities"""
    logger.info("Starting cost optimization analysis")
    
    try:
        # Initialize optimizer
        optimizer = KubernetesCostOptimizer(
            kubeconfig_path=kubeconfig,
            history_file=os.path.expanduser(history_file),
            cloud_provider=cloud_provider
        )
        
        # Collect current metrics
        optimizer._collect_current_metrics()
        
        # Run analysis
        suggestions = optimizer.analyze_cost_optimization()
        
        total_savings = 0.0
        for suggestion in suggestions:
            savings = suggestion.estimated_savings.get('total_monthly', 0)
            if isinstance(savings, (int, float)):
                total_savings += savings
        
        # Display results
        if output_format == "json":
            import json
            result = {
                "suggestions": [s.to_dict() for s in suggestions],
                "total_monthly_savings": round(total_savings, 2)
            }
            print(json.dumps(result, indent=2))
        else:
            console.print(f"\n[bold]Cost Optimization Results:[/bold]")
            console.print(f"Found [bold]{len(suggestions)}[/bold] optimization opportunities")
            console.print(f"Estimated monthly savings: [bold green]${round(total_savings, 2)}[/bold green]")
            
            if suggestions:
                console.print("\n[bold]Optimization Suggestions:[/bold]")
                for i, suggestion in enumerate(suggestions):
                    priority_color = {
                        "high": "red",
                        "medium": "yellow",
                        "low": "blue"
                    }.get(suggestion.priority, "white")
                    
                    console.print(f"\n  {i+1}. [[bold {priority_color}]{suggestion.priority}[/bold {priority_color}]] {suggestion.resource_type}/{suggestion.namespace}/{suggestion.name}")
                    
                    console.print("    Current Allocation:")
                    for k, v in suggestion.current_allocation.items():
                        console.print(f"      {k}: {v}")
                    
                    console.print("    Suggested Allocation:")
                    for k, v in suggestion.suggested_allocation.items():
                        console.print(f"      {k}: {v}")
                    
                    console.print("    Estimated Savings:")
                    for k, v in suggestion.estimated_savings.items():
                        if k == "total_monthly":
                            console.print(f"      {k}: [green]${v}[/green]")
                        else:
                            console.print(f"      {k}: {v}")
                    
                    console.print(f"    Confidence: {int(suggestion.confidence * 100)}%")
    
    except Exception as e:
        logger.error(f"Error performing cost optimization: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

@app.command()
def backup_resources(
    name: str = typer.Option(..., help="Name for this backup"),
    namespaces: str = typer.Option("all", help="Comma-separated list of namespaces to backup (default: all)"),
    resource_types: str = typer.Option("all", help="Comma-separated list of resource types to backup (default: all)"),
    include_labels: str = typer.Option(None, help="Comma-separated list of labels to include (format: key=value)"),
    exclude_labels: str = typer.Option(None, help="Comma-separated list of labels to exclude (format: key=value)"),
    kubeconfig: str = typer.Option(None, help="Path to kubeconfig file"),
    backup_dir: str = typer.Option("~/.kagent/backups", help="Directory to store backups"),
    history_file: str = typer.Option("~/.kagent/backup_history.json", help="Path to store backup history"),
):
    """Create a backup of Kubernetes resources"""
    logger.info(f"Starting backup: {name}")
    
    try:
        # Parse namespaces and resource types
        namespace_list = [ns.strip() for ns in namespaces.split(",")]
        resource_type_list = [rt.strip() for rt in resource_types.split(",")]
        
        # Parse labels
        include_label_dict = {}
        if include_labels:
            for label in include_labels.split(","):
                key, value = label.split("=", 1)
                include_label_dict[key.strip()] = value.strip()
        
        exclude_label_dict = {}
        if exclude_labels:
            for label in exclude_labels.split(","):
                key, value = label.split("=", 1)
                exclude_label_dict[key.strip()] = value.strip()
        
        # Initialize backup manager
        backup_manager = KubernetesBackupManager(
            kubeconfig_path=kubeconfig,
            backup_dir=os.path.expanduser(backup_dir),
            history_file=os.path.expanduser(history_file)
        )
        
        # Create backup job
        backup_id = str(uuid.uuid4())
        job = BackupJob(
            id=backup_id,
            name=name,
            namespaces=namespace_list,
            resource_types=resource_type_list,
            include_labels=include_label_dict,
            exclude_labels=exclude_label_dict
        )
        
        # Run backup
        console.print("[bold]Starting backup...[/bold]")
        result = backup_manager.create_backup(job)
        
        # Display results
        if result.status == "completed":
            console.print(f"\n[bold green]Backup completed successfully[/bold green]")
            console.print(f"Backup ID: {result.id}")
            console.print(f"Backup Name: {result.name}")
            console.print(f"Resources backed up:")
            
            for resource_type, count in result.resources_backed_up.items():
                console.print(f"  {resource_type}: {count}")
            
            file_size_mb = result.file_size / (1024 * 1024) if result.file_size else 0
            console.print(f"Backup file size: {file_size_mb:.2f} MB")
        else:
            console.print(f"\n[bold red]Backup failed[/bold red]")
            console.print(f"Error: {result.error_message}")
    
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

@app.command()
def list_backups(
    kubeconfig: str = typer.Option(None, help="Path to kubeconfig file"),
    backup_dir: str = typer.Option("~/.kagent/backups", help="Directory with backups"),
    history_file: str = typer.Option("~/.kagent/backup_history.json", help="Path to backup history file"),
    output_format: str = typer.Option("table", help="Output format: table, json")
):
    """List available backups"""
    try:
        # Initialize backup manager
        backup_manager = KubernetesBackupManager(
            kubeconfig_path=kubeconfig,
            backup_dir=os.path.expanduser(backup_dir),
            history_file=os.path.expanduser(history_file)
        )
        
        # Get backup list
        backups = backup_manager.get_backup_list()
        
        # Display results
        if output_format == "json":
            import json
            print(json.dumps(backups, indent=2))
        else:
            console.print(f"\n[bold]Available Backups:[/bold]")
            if not backups:
                console.print("No backups found")
                return
            
            for backup in backups:
                status_color = {
                    "completed": "green",
                    "failed": "red",
                    "running": "yellow",
                    "pending": "blue"
                }.get(backup["status"], "white")
                
                file_info = backup_manager.get_backup_file_info(backup["id"])
                file_size = f"{file_info['size'] / (1024 * 1024):.2f} MB" if file_info else "N/A"
                
                console.print(f"\n  ID: {backup['id']}")
                console.print(f"  Name: {backup['name']}")
                console.print(f"  Status: [bold {status_color}]{backup['status']}[/bold {status_color}]")
                console.print(f"  Created: {backup['timestamp']}")
                console.print(f"  Namespaces: {', '.join(backup['namespaces'])}")
                console.print(f"  Resource Types: {', '.join(backup['resource_types'])}")
                console.print(f"  File Size: {file_size}")
                
                if backup['resources_backed_up']:
                    console.print("  Resources Backed Up:")
                    for resource_type, count in backup['resources_backed_up'].items():
                        console.print(f"    {resource_type}: {count}")
    
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

@app.command()
def restore_backup(
    backup_id: str = typer.Option(..., help="ID of the backup to restore"),
    name: str = typer.Option(..., help="Name for this restore operation"),
    namespaces: str = typer.Option("all", help="Comma-separated list of namespaces to restore (default: all)"),
    resource_types: str = typer.Option("all", help="Comma-separated list of resource types to restore (default: all)"),
    include_labels: str = typer.Option(None, help="Comma-separated list of labels to include (format: key=value)"),
    exclude_labels: str = typer.Option(None, help="Comma-separated list of labels to exclude (format: key=value)"),
    restore_strategy: str = typer.Option("create_or_replace", help="Restore strategy: create_or_replace, create_only, replace_only"),
    kubeconfig: str = typer.Option(None, help="Path to kubeconfig file"),
    backup_dir: str = typer.Option("~/.kagent/backups", help="Directory with backups"),
    history_file: str = typer.Option("~/.kagent/backup_history.json", help="Path to backup history file"),
):
    """Restore resources from a backup"""
    logger.info(f"Starting restore from backup {backup_id}")
    
    try:
        # Parse namespaces and resource types
        namespace_list = [ns.strip() for ns in namespaces.split(",")]
        resource_type_list = [rt.strip() for rt in resource_types.split(",")]
        
        # Parse labels
        include_label_dict = {}
        if include_labels:
            for label in include_labels.split(","):
                key, value = label.split("=", 1)
                include_label_dict[key.strip()] = value.strip()
        
        exclude_label_dict = {}
        if exclude_labels:
            for label in exclude_labels.split(","):
                key, value = label.split("=", 1)
                exclude_label_dict[key.strip()] = value.strip()
        
        # Initialize backup manager
        backup_manager = KubernetesBackupManager(
            kubeconfig_path=kubeconfig,
            backup_dir=os.path.expanduser(backup_dir),
            history_file=os.path.expanduser(history_file)
        )
        
        # Check if backup exists
        backup = backup_manager.get_backup_job(backup_id)
        if not backup:
            console.print(f"[bold red]Error:[/bold red] Backup with ID {backup_id} not found")
            sys.exit(1)
        
        # Create restore job
        restore_id = str(uuid.uuid4())
        job = RestoreJob(
            id=restore_id,
            backup_id=backup_id,
            name=name,
            namespaces=namespace_list,
            resource_types=resource_type_list if resource_types != "all" else None,
            include_labels=include_label_dict,
            exclude_labels=exclude_label_dict,
            restore_strategy=restore_strategy
        )
        
        # Run restore
        console.print("[bold]Starting restore...[/bold]")
        result = backup_manager.restore_from_backup(job)
        
        # Display results
        if result.status == "completed":
            console.print(f"\n[bold green]Restore completed successfully[/bold green]")
            console.print(f"Restore ID: {result.id}")
            console.print(f"Restore Name: {result.name}")
            console.print(f"Resources restored:")
            
            for resource_type, count in result.resources_restored.items():
                console.print(f"  {resource_type}: {count}")
        else:
            console.print(f"\n[bold red]Restore failed[/bold red]")
            console.print(f"Error: {result.error_message}")
    
    except Exception as e:
        logger.error(f"Error restoring from backup: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

@app.command()
def train_model(
    output_path: str = typer.Option(None, help="Path to save the trained model"),
    contamination: float = typer.Option(0.1, help="Expected proportion of anomalies in the data"),
):
    """
    Train a machine learning model for Kubernetes cluster predictions.
    
    This command trains an Isolation Forest model to detect anomalies in Kubernetes
    cluster metrics and saves it to be used by the predictor agent.
    """
    try:
        model_path = train_and_save_model(output_path, contamination)
        console.print(f"[green]Model successfully trained and saved to:[/green] {model_path}")
    except Exception as e:
        console.print(f"[red]Error training model:[/red] {str(e)}")
        raise typer.Exit(code=1)

def run():
    app()


if __name__ == "__main__":
    run()
