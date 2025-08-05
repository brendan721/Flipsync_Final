"""Example script showing how to use the ConfigManager.

This script demonstrates the main features of the ConfigManager
including environment-aware configuration, validation, and change listeners.
"""

import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Import our ConfigManager
from fs_agt.core.config.config_manager import ConfigManager


def main():
    """Example of using the ConfigManager."""
    logger = logging.getLogger(__name__)

    # Create config directory if it doesn't exist
    config_dir = Path(__file__).parent

    # Get the singleton instance with default settings
    logger.info("Initializing ConfigManager...")
    config_manager = ConfigManager(
        config_dir=config_dir, environment="development", auto_reload=True
    )

    # Load example config
    config_manager.load("example_config.yaml")

    # Validate against schema
    logger.info("Validating configuration against schema...")
    validation_result = config_manager.validate()

    if validation_result.is_valid:
        logger.info("Configuration is valid!")
    else:
        logger.error(
            "Configuration validation failed with errors: %s", validation_result.errors
        )
        for warning in validation_result.warnings:
            logger.warning("Validation warning: %s", warning)

    # Example of getting a configuration value
    app_name = config_manager.get("app.name")
    logger.info("App name: %s", app_name)

    # Example of getting a section of configuration
    database_config = config_manager.get_section("database")
    logger.info("Database configuration: %s", database_config)

    # Example of setting a configuration value
    config_manager.set("app.debug", True)
    logger.info("Updated app.debug to %s", config_manager.get("app.debug"))

    # Example of environment-specific configuration
    current_env = config_manager.get_environment()
    logger.info("Current environment: %s", current_env)

    # Example of registering a change listener
    def config_change_listener(key, value):
        logger.info("Configuration changed: %s = %s", key, value)

    config_manager.register_change_listener(config_change_listener)

    # Example of changing environment
    logger.info("Changing environment to production...")
    config_manager.set_environment("production")

    # Show environment-specific changes
    logger.info(
        "Database type after environment change: %s",
        config_manager.get("database.type"),
    )
    logger.info(
        "App debug mode after environment change: %s", config_manager.get("app.debug")
    )

    # Example of setting a configuration value that will trigger the listener
    config_manager.set("agent.temperature", 0.5)

    # Example of config validation with custom schema
    custom_schema = {
        "agent": {
            "type": "object",
            "properties": {
                "temperature": {
                    "type": "float",
                    "constraints": {"min": 0.1, "max": 0.9},
                }
            },
        }
    }

    validation_result = config_manager.validate(custom_schema)
    if validation_result.is_valid:
        logger.info("Custom validation passed!")
    else:
        logger.error(
            "Custom validation failed with errors: %s", validation_result.errors
        )


if __name__ == "__main__":
    main()
