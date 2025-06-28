"""
Deployment verification tests for FlipSync.

This module implements comprehensive deployment verification tests
for the FlipSync system, ensuring that deployments are successful
and meet all requirements.
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Status of a verification test."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class VerificationResult:
    """Result of a verification test."""

    def __init__(
        self,
        test_name: str,
        status: VerificationStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.test_name = test_name
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "test_name": self.test_name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class SystemAuditor:
    """Audits the deployed FlipSync system."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        namespace: str = "flipsync",
        context: Optional[str] = None,
    ):
        self.config_path = config_path
        self.namespace = namespace
        self.context = context
        self.results: List[VerificationResult] = []
        self.k8s_client = None
        self.core_v1 = None
        self.apps_v1 = None
        self.networking_v1 = None
        self.batch_v1 = None

    def initialize(self) -> None:
        """Initialize the auditor."""
        try:
            # Load Kubernetes configuration
            if self.config_path:
                config.load_kube_config(
                    config_file=self.config_path, context=self.context
                )
            else:
                try:
                    config.load_kube_config(context=self.context)
                except kubernetes.config.config_exception.ConfigException:
                    config.load_incluster_config()

            # Create API clients
            self.k8s_client = client.ApiClient()
            self.core_v1 = client.CoreV1Api(self.k8s_client)
            self.apps_v1 = client.AppsV1Api(self.k8s_client)
            self.networking_v1 = client.NetworkingV1Api(self.k8s_client)
            self.batch_v1 = client.BatchV1Api(self.k8s_client)

            logger.info("Initialized Kubernetes client")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def run_all_tests(self) -> List[VerificationResult]:
        """Run all verification tests."""
        if not self.k8s_client:
            self.initialize()

        # Run tests
        self.verify_namespace()
        self.verify_deployments()
        self.verify_services()
        self.verify_ingresses()
        self.verify_configmaps()
        self.verify_secrets()
        self.verify_persistent_volumes()
        self.verify_resource_usage()
        self.verify_pod_health()
        self.verify_logs()
        self.verify_custom_resources()

        return self.results

    def verify_namespace(self) -> VerificationResult:
        """Verify that the namespace exists."""
        try:
            self.core_v1.read_namespace(self.namespace)
            result = VerificationResult(
                test_name="namespace_exists",
                status=VerificationStatus.PASSED,
                message=f"Namespace {self.namespace} exists",
            )
        except ApiException as e:
            if e.status == 404:
                result = VerificationResult(
                    test_name="namespace_exists",
                    status=VerificationStatus.FAILED,
                    message=f"Namespace {self.namespace} does not exist",
                    details={"error": str(e)},
                )
            else:
                result = VerificationResult(
                    test_name="namespace_exists",
                    status=VerificationStatus.FAILED,
                    message=f"Error checking namespace {self.namespace}",
                    details={"error": str(e)},
                )

        self.results.append(result)
        return result

    def verify_deployments(self) -> VerificationResult:
        """Verify that all required deployments exist and are ready."""
        required_deployments = {
            "flipsync-api": 1,
            "flipsync-worker": 2,
            "flipsync-db": 1,
            "flipsync-redis": 1,
            "flipsync-frontend": 1,
        }

        try:
            deployments = self.apps_v1.list_namespaced_deployment(self.namespace)
            existing_deployments = {d.metadata.name: d for d in deployments.items}

            missing_deployments = []
            not_ready_deployments = []

            for name, min_replicas in required_deployments.items():
                if name not in existing_deployments:
                    missing_deployments.append(name)
                    continue

                deployment = existing_deployments[name]
                if (
                    deployment.status.ready_replicas is None
                    or deployment.status.ready_replicas < min_replicas
                ):
                    not_ready_deployments.append(
                        f"{name} (ready: {deployment.status.ready_replicas or 0}, required: {min_replicas})"
                    )

            if missing_deployments or not_ready_deployments:
                status = VerificationStatus.FAILED
                message = "Some deployments are missing or not ready"
                details = {
                    "missing_deployments": missing_deployments,
                    "not_ready_deployments": not_ready_deployments,
                }
            else:
                status = VerificationStatus.PASSED
                message = "All required deployments exist and are ready"
                details = {
                    "deployments": [d.metadata.name for d in deployments.items],
                }

            result = VerificationResult(
                test_name="deployments_ready",
                status=status,
                message=message,
                details=details,
            )
        except ApiException as e:
            result = VerificationResult(
                test_name="deployments_ready",
                status=VerificationStatus.FAILED,
                message=f"Error checking deployments in namespace {self.namespace}",
                details={"error": str(e)},
            )

        self.results.append(result)
        return result

    def verify_services(self) -> VerificationResult:
        """Verify that all required services exist."""
        required_services = [
            "flipsync-api",
            "flipsync-worker",
            "flipsync-db",
            "flipsync-redis",
            "flipsync-frontend",
        ]

        try:
            services = self.core_v1.list_namespaced_service(self.namespace)
            existing_services = [s.metadata.name for s in services.items]

            missing_services = [
                name for name in required_services if name not in existing_services
            ]

            if missing_services:
                status = VerificationStatus.FAILED
                message = "Some services are missing"
                details = {
                    "missing_services": missing_services,
                }
            else:
                status = VerificationStatus.PASSED
                message = "All required services exist"
                details = {
                    "services": existing_services,
                }

            result = VerificationResult(
                test_name="services_exist",
                status=status,
                message=message,
                details=details,
            )
        except ApiException as e:
            result = VerificationResult(
                test_name="services_exist",
                status=VerificationStatus.FAILED,
                message=f"Error checking services in namespace {self.namespace}",
                details={"error": str(e)},
            )

        self.results.append(result)
        return result

    def verify_ingresses(self) -> VerificationResult:
        """Verify that all required ingresses exist."""
        required_ingresses = [
            "flipsync-api",
            "flipsync-frontend",
        ]

        try:
            ingresses = self.networking_v1.list_namespaced_ingress(self.namespace)
            existing_ingresses = [i.metadata.name for i in ingresses.items]

            missing_ingresses = [
                name for name in required_ingresses if name not in existing_ingresses
            ]

            if missing_ingresses:
                status = VerificationStatus.FAILED
                message = "Some ingresses are missing"
                details = {
                    "missing_ingresses": missing_ingresses,
                }
            else:
                status = VerificationStatus.PASSED
                message = "All required ingresses exist"
                details = {
                    "ingresses": existing_ingresses,
                }

            result = VerificationResult(
                test_name="ingresses_exist",
                status=status,
                message=message,
                details=details,
            )
        except ApiException as e:
            result = VerificationResult(
                test_name="ingresses_exist",
                status=VerificationStatus.FAILED,
                message=f"Error checking ingresses in namespace {self.namespace}",
                details={"error": str(e)},
            )

        self.results.append(result)
        return result

    def verify_configmaps(self) -> VerificationResult:
        """Verify that all required configmaps exist."""
        required_configmaps = [
            "flipsync-config",
            "flipsync-env",
        ]

        try:
            configmaps = self.core_v1.list_namespaced_config_map(self.namespace)
            existing_configmaps = [c.metadata.name for c in configmaps.items]

            missing_configmaps = [
                name for name in required_configmaps if name not in existing_configmaps
            ]

            if missing_configmaps:
                status = VerificationStatus.FAILED
                message = "Some configmaps are missing"
                details = {
                    "missing_configmaps": missing_configmaps,
                }
            else:
                status = VerificationStatus.PASSED
                message = "All required configmaps exist"
                details = {
                    "configmaps": existing_configmaps,
                }

            result = VerificationResult(
                test_name="configmaps_exist",
                status=status,
                message=message,
                details=details,
            )
        except ApiException as e:
            result = VerificationResult(
                test_name="configmaps_exist",
                status=VerificationStatus.FAILED,
                message=f"Error checking configmaps in namespace {self.namespace}",
                details={"error": str(e)},
            )

        self.results.append(result)
        return result

    def verify_secrets(self) -> VerificationResult:
        """Verify that all required secrets exist."""
        required_secrets = [
            "flipsync-db-credentials",
            "flipsync-api-keys",
            "flipsync-tls",
        ]

        try:
            secrets = self.core_v1.list_namespaced_secret(self.namespace)
            existing_secrets = [s.metadata.name for s in secrets.items]

            missing_secrets = [
                name for name in required_secrets if name not in existing_secrets
            ]

            if missing_secrets:
                status = VerificationStatus.FAILED
                message = "Some secrets are missing"
                details = {
                    "missing_secrets": missing_secrets,
                }
            else:
                status = VerificationStatus.PASSED
                message = "All required secrets exist"
                details = {
                    "secrets": existing_secrets,
                }

            result = VerificationResult(
                test_name="secrets_exist",
                status=status,
                message=message,
                details=details,
            )
        except ApiException as e:
            result = VerificationResult(
                test_name="secrets_exist",
                status=VerificationStatus.FAILED,
                message=f"Error checking secrets in namespace {self.namespace}",
                details={"error": str(e)},
            )

        self.results.append(result)
        return result

    def verify_persistent_volumes(self) -> VerificationResult:
        """Verify that all required persistent volumes exist and are bound."""
        try:
            pvcs = self.core_v1.list_namespaced_persistent_volume_claim(self.namespace)
            unbound_pvcs = []

            for pvc in pvcs.items:
                if pvc.status.phase != "Bound":
                    unbound_pvcs.append(
                        f"{pvc.metadata.name} (status: {pvc.status.phase})"
                    )

            if unbound_pvcs:
                status = VerificationStatus.FAILED
                message = "Some persistent volume claims are not bound"
                details = {
                    "unbound_pvcs": unbound_pvcs,
                }
            else:
                status = VerificationStatus.PASSED
                message = "All persistent volume claims are bound"
                details = {
                    "pvcs": [pvc.metadata.name for pvc in pvcs.items],
                }

            result = VerificationResult(
                test_name="persistent_volumes_bound",
                status=status,
                message=message,
                details=details,
            )
        except ApiException as e:
            result = VerificationResult(
                test_name="persistent_volumes_bound",
                status=VerificationStatus.FAILED,
                message=f"Error checking persistent volumes in namespace {self.namespace}",
                details={"error": str(e)},
            )

        self.results.append(result)
        return result

    def verify_resource_usage(self) -> VerificationResult:
        """Verify resource usage of pods."""
        try:
            pods = self.core_v1.list_namespaced_pod(self.namespace)
            resource_issues = []

            for pod in pods.items:
                if pod.status.phase != "Running":
                    continue

                for container in pod.spec.containers:
                    if not container.resources or not container.resources.limits:
                        resource_issues.append(
                            f"{pod.metadata.name}/{container.name} has no resource limits"
                        )

            if resource_issues:
                status = VerificationStatus.WARNING
                message = "Some containers have resource issues"
                details = {
                    "resource_issues": resource_issues,
                }
            else:
                status = VerificationStatus.PASSED
                message = "All containers have proper resource limits"
                details = {
                    "pods": [
                        pod.metadata.name
                        for pod in pods.items
                        if pod.status.phase == "Running"
                    ],
                }

            result = VerificationResult(
                test_name="resource_usage",
                status=status,
                message=message,
                details=details,
            )
        except ApiException as e:
            result = VerificationResult(
                test_name="resource_usage",
                status=VerificationStatus.FAILED,
                message=f"Error checking resource usage in namespace {self.namespace}",
                details={"error": str(e)},
            )

        self.results.append(result)
        return result

    def verify_pod_health(self) -> VerificationResult:
        """Verify health of pods."""
        try:
            pods = self.core_v1.list_namespaced_pod(self.namespace)
            unhealthy_pods = []

            for pod in pods.items:
                if pod.status.phase not in ["Running", "Succeeded"]:
                    unhealthy_pods.append(
                        f"{pod.metadata.name} (status: {pod.status.phase})"
                    )
                    continue

                if pod.status.phase == "Running":
                    for container_status in pod.status.container_statuses:
                        if not container_status.ready:
                            restart_count = container_status.restart_count
                            unhealthy_pods.append(
                                f"{pod.metadata.name}/{container_status.name} not ready (restarts: {restart_count})"
                            )

            if unhealthy_pods:
                status = VerificationStatus.FAILED
                message = "Some pods are unhealthy"
                details = {
                    "unhealthy_pods": unhealthy_pods,
                }
            else:
                status = VerificationStatus.PASSED
                message = "All pods are healthy"
                details = {
                    "pods": [pod.metadata.name for pod in pods.items],
                }

            result = VerificationResult(
                test_name="pod_health",
                status=status,
                message=message,
                details=details,
            )
        except ApiException as e:
            result = VerificationResult(
                test_name="pod_health",
                status=VerificationStatus.FAILED,
                message=f"Error checking pod health in namespace {self.namespace}",
                details={"error": str(e)},
            )

        self.results.append(result)
        return result

    def verify_logs(self) -> VerificationResult:
        """Verify logs for errors."""
        try:
            pods = self.core_v1.list_namespaced_pod(self.namespace)
            pods_with_errors = []

            for pod in pods.items:
                if pod.status.phase != "Running":
                    continue

                for container in pod.spec.containers:
                    try:
                        logs = self.core_v1.read_namespaced_pod_log(
                            name=pod.metadata.name,
                            namespace=self.namespace,
                            container=container.name,
                            tail_lines=100,
                        )

                        error_count = logs.lower().count("error")
                        exception_count = logs.lower().count("exception")
                        fatal_count = logs.lower().count("fatal")

                        if error_count > 5 or exception_count > 0 or fatal_count > 0:
                            pods_with_errors.append(
                                f"{pod.metadata.name}/{container.name} "
                                f"(errors: {error_count}, exceptions: {exception_count}, fatal: {fatal_count})"
                            )
                    except ApiException:
                        # Skip if logs can't be retrieved
                        pass

            if pods_with_errors:
                status = VerificationStatus.WARNING
                message = "Some pods have errors in logs"
                details = {
                    "pods_with_errors": pods_with_errors,
                }
            else:
                status = VerificationStatus.PASSED
                message = "No significant errors found in logs"
                details = {}

            result = VerificationResult(
                test_name="logs_check",
                status=status,
                message=message,
                details=details,
            )
        except ApiException as e:
            result = VerificationResult(
                test_name="logs_check",
                status=VerificationStatus.FAILED,
                message=f"Error checking logs in namespace {self.namespace}",
                details={"error": str(e)},
            )

        self.results.append(result)
        return result

    def verify_custom_resources(self) -> VerificationResult:
        """Verify custom resources."""
        # This is a placeholder for custom resource verification
        # In a real implementation, this would check specific CRDs
        result = VerificationResult(
            test_name="custom_resources",
            status=VerificationStatus.SKIPPED,
            message="Custom resource verification not implemented",
        )

        self.results.append(result)
        return result

    def verify_deployment_against_requirements(
        self, requirements: Dict[str, Any]
    ) -> List[VerificationResult]:
        """Verify deployment against specific requirements."""
        if not self.k8s_client:
            self.initialize()

        results = []
        missing_components = []

        # Check required deployments
        if "deployments" in requirements:
            for namespace, deployments in requirements["deployments"].items():
                try:
                    existing_deployments = self.apps_v1.list_namespaced_deployment(
                        namespace
                    )
                    existing_deployment_names = [
                        d.metadata.name for d in existing_deployments.items
                    ]

                    for deployment in deployments:
                        if deployment not in existing_deployment_names:
                            missing_components.append(
                                f"deployment {deployment} in namespace {namespace}"
                            )
                except ApiException as e:
                    missing_components.append(
                        f"deployments in namespace {namespace} (error: {e})"
                    )

        # Check required services
        if "services" in requirements:
            for namespace, services in requirements["services"].items():
                try:
                    existing_services = self.core_v1.list_namespaced_service(namespace)
                    existing_service_names = [
                        s.metadata.name for s in existing_services.items
                    ]

                    for service in services:
                        if service not in existing_service_names:
                            missing_components.append(
                                f"service {service} in namespace {namespace}"
                            )
                except ApiException as e:
                    missing_components.append(
                        f"services in namespace {namespace} (error: {e})"
                    )

        # Check ingresses
        if "ingresses" in requirements:
            for namespace, ingresses in requirements["ingresses"].items():
                try:
                    existing_ingresses = self.networking_v1.list_namespaced_ingress(
                        namespace
                    )
                    existing_ingress_names = [
                        i.metadata.name for i in existing_ingresses.items
                    ]

                    for ingress in ingresses:
                        if ingress not in existing_ingress_names:
                            missing_components.append(
                                f"ingress {ingress} in namespace {namespace}"
                            )
                except ApiException as e:
                    missing_components.append(
                        f"ingresses in namespace {namespace} (error: {e})"
                    )

        # Check configmaps
        if "configmaps" in requirements:
            for namespace, configmaps in requirements["configmaps"].items():
                try:
                    existing_configmaps = self.core_v1.list_namespaced_config_map(
                        namespace
                    )
                    existing_configmap_names = [
                        c.metadata.name for c in existing_configmaps.items
                    ]

                    for configmap in configmaps:
                        if configmap not in existing_configmap_names:
                            missing_components.append(
                                f"configmap {configmap} in namespace {namespace}"
                            )
                except ApiException as e:
                    missing_components.append(
                        f"configmaps in namespace {namespace} (error: {e})"
                    )

        # Check secrets
        if "secrets" in requirements:
            for namespace, secrets in requirements["secrets"].items():
                try:
                    existing_secrets = self.core_v1.list_namespaced_secret(namespace)
                    existing_secret_names = [
                        s.metadata.name for s in existing_secrets.items
                    ]

                    for secret in secrets:
                        if secret not in existing_secret_names:
                            missing_components.append(
                                f"secret {secret} in namespace {namespace}"
                            )
                except ApiException as e:
                    missing_components.append(
                        f"secrets in namespace {namespace} (error: {e})"
                    )

        # Create result
        if missing_components:
            result = VerificationResult(
                test_name="deployment_requirements",
                status=VerificationStatus.FAILED,
                message="Some required components are missing",
                details={"missing_components": missing_components},
            )
        else:
            result = VerificationResult(
                test_name="deployment_requirements",
                status=VerificationStatus.PASSED,
                message="All required components are present",
                details={"requirements": requirements},
            )

        results.append(result)
        self.results.extend(results)
        return results

    def generate_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate a report of verification results."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "namespace": self.namespace,
            "results": [result.to_dict() for result in self.results],
            "summary": {
                "total": len(self.results),
                "passed": len(
                    [r for r in self.results if r.status == VerificationStatus.PASSED]
                ),
                "failed": len(
                    [r for r in self.results if r.status == VerificationStatus.FAILED]
                ),
                "warning": len(
                    [r for r in self.results if r.status == VerificationStatus.WARNING]
                ),
                "skipped": len(
                    [r for r in self.results if r.status == VerificationStatus.SKIPPED]
                ),
            },
        }

        if output_path:
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)

        return report


def main():
    """Run the system auditor from the command line."""
    parser = argparse.ArgumentParser(description="FlipSync System Auditor")
    parser.add_argument("--config", help="Path to kubeconfig file")
    parser.add_argument("--namespace", default="flipsync", help="Kubernetes namespace")
    parser.add_argument("--context", help="Kubernetes context")
    parser.add_argument("--output", help="Output path for report")
    parser.add_argument("--requirements", help="Path to requirements file")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create auditor
    auditor = SystemAuditor(
        config_path=args.config,
        namespace=args.namespace,
        context=args.context,
    )

    # Run tests
    if args.requirements:
        with open(args.requirements, "r") as f:
            requirements = json.load(f)
        auditor.verify_deployment_against_requirements(requirements)
    else:
        auditor.run_all_tests()

    # Generate report
    report = auditor.generate_report(args.output)

    # Print summary
    print(f"Total tests: {report['summary']['total']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Warning: {report['summary']['warning']}")
    print(f"Skipped: {report['summary']['skipped']}")

    # Exit with error if any tests failed
    if report["summary"]["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
