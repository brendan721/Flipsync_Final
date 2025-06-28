#!/usr/bin/env python3
"""
Architecture Preservation Validator for FlipSync
Ensures the sophisticated 35+ agent and 225+ service architecture is maintained
"""

import os
import sys
from pathlib import Path

# Architecture thresholds from baseline (exact values from baseline script)
MINIMUM_AGENTS = 35
MINIMUM_SERVICES = 225
MINIMUM_DB_MODELS = 30
MINIMUM_API_ROUTES = 37


def count_agents():
    """Count agent files in the system using same method as baseline"""
    import subprocess

    try:
        result = subprocess.run(
            ["find", "fs_agt_clean/agents/", "-name", "*agent*.py", "-type", "f"],
            capture_output=True,
            text=True,
        )
        agent_files = [
            line.strip() for line in result.stdout.split("\n") if line.strip()
        ]
        return len(agent_files)
    except:
        # Fallback method
        agent_files = []
        for root, dirs, files in os.walk("fs_agt_clean/agents"):
            for file in files:
                if "agent" in file and file.endswith(".py"):
                    agent_files.append(os.path.join(root, file))
        return len(agent_files)


def count_services():
    """Count service files using exact same method as baseline script"""
    import subprocess

    try:
        # Use exact same command as baseline script
        result = subprocess.run(
            [
                "sh",
                "-c",
                "find fs_agt_clean/services/ -name '*.py' | grep -v __init__ | wc -l",
            ],
            capture_output=True,
            text=True,
        )
        return int(result.stdout.strip())
    except:
        # Fallback method
        service_files = []
        for root, dirs, files in os.walk("fs_agt_clean/services"):
            for file in files:
                if (
                    file.endswith(".py")
                    and not file.startswith("test_")
                    and file != "__init__.py"
                ):
                    service_files.append(os.path.join(root, file))
        return len(service_files)


def count_db_models():
    """Count database model files using exact same method as baseline script"""
    import subprocess

    try:
        # Use exact same command as baseline script
        result = subprocess.run(
            [
                "sh",
                "-c",
                "find fs_agt_clean/database/models/ -name '*.py' 2>/dev/null | grep -v __init__ | wc -l",
            ],
            capture_output=True,
            text=True,
        )
        return int(result.stdout.strip())
    except:
        # Fallback method
        model_files = []
        models_dir = "fs_agt_clean/database/models"
        if os.path.exists(models_dir):
            for file in os.listdir(models_dir):
                if (
                    file.endswith(".py")
                    and not file.startswith("test_")
                    and file != "__init__.py"
                ):
                    model_files.append(file)
        return len(model_files)


def count_api_routes():
    """Count API route modules using exact same method as baseline script"""
    import subprocess

    try:
        # Use exact same command as baseline script
        result = subprocess.run(
            [
                "sh",
                "-c",
                "find fs_agt_clean/api/routes/ -name '*.py' 2>/dev/null | grep -v __init__ | wc -l",
            ],
            capture_output=True,
            text=True,
        )
        return int(result.stdout.strip())
    except:
        # Fallback method
        route_files = []
        routes_dir = "fs_agt_clean/api/routes"
        if os.path.exists(routes_dir):
            for root, dirs, files in os.walk(routes_dir):
                for file in files:
                    if (
                        file.endswith(".py")
                        and not file.startswith("test_")
                        and file != "__init__.py"
                    ):
                        route_files.append(os.path.join(root, file))
        return len(route_files)


def validate_architecture():
    """Validate that architecture complexity is preserved"""
    print("=== FlipSync Architecture Preservation Check ===")

    # Count current architecture components
    agent_count = count_agents()
    service_count = count_services()
    model_count = count_db_models()
    route_count = count_api_routes()

    print(f"Current Architecture Metrics:")
    print(f"  Agents: {agent_count} (minimum: {MINIMUM_AGENTS})")
    print(f"  Services: {service_count} (minimum: {MINIMUM_SERVICES})")
    print(f"  DB Models: {model_count} (minimum: {MINIMUM_DB_MODELS})")
    print(f"  API Routes: {route_count} (minimum: {MINIMUM_API_ROUTES})")
    print()

    # Validation checks
    violations = []

    if agent_count < MINIMUM_AGENTS:
        violations.append(
            f"Agent count ({agent_count}) below minimum ({MINIMUM_AGENTS})"
        )

    if service_count < MINIMUM_SERVICES:
        violations.append(
            f"Service count ({service_count}) below minimum ({MINIMUM_SERVICES})"
        )

    if model_count < MINIMUM_DB_MODELS:
        violations.append(
            f"DB model count ({model_count}) below minimum ({MINIMUM_DB_MODELS})"
        )

    if route_count < MINIMUM_API_ROUTES:
        violations.append(
            f"API route count ({route_count}) below minimum ({MINIMUM_API_ROUTES})"
        )

    if violations:
        print("❌ ARCHITECTURE PRESERVATION VIOLATIONS:")
        for violation in violations:
            print(f"  - {violation}")
        print()
        print("The sophisticated FlipSync architecture has been compromised!")
        print("This complexity is INTENTIONAL and serves legitimate business needs.")
        print("Please restore the removed components.")
        return False
    else:
        print("✅ Architecture preservation validated successfully")
        print("All architectural complexity thresholds maintained")
        return True


def check_critical_files():
    """Check that critical architectural files exist"""
    critical_files = [
        "fs_agt_clean/agents/executive/executive_agent.py",
        "fs_agt_clean/agents/market/market_agent.py",
        "fs_agt_clean/agents/content/content_agent.py",
        "fs_agt_clean/agents/logistics/logistics_agent.py",
        "fs_agt_clean/services/advanced_features/__init__.py",
        "fs_agt_clean/services/infrastructure/__init__.py",
        "fs_agt_clean/services/communication/__init__.py",
    ]

    missing_files = []
    for file_path in critical_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("❌ CRITICAL FILES MISSING:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    else:
        print("✅ All critical architectural files present")
        return True


def main():
    """Main validation function"""
    architecture_valid = validate_architecture()
    files_valid = check_critical_files()

    if architecture_valid and files_valid:
        print("\n🎉 FlipSync architecture preservation validated successfully!")
        print("The enterprise-grade complexity has been maintained.")
        sys.exit(0)
    else:
        print("\n💥 Architecture preservation check FAILED!")
        print("FlipSync's sophisticated architecture has been compromised.")
        sys.exit(1)


if __name__ == "__main__":
    main()
