"""
FlipSync Architecture Module
===========================

Provides architectural boundaries and validation for the 4+1 system.
"""

from .boundaries import (
    ArchitecturalBoundaries,
    ArchitectureValidator,
    ArchitecturalLayer,
    validate_agent_architecture,
    validate_agent_communication,
    create_architecture_validator
)

__all__ = [
    "ArchitecturalBoundaries",
    "ArchitectureValidator", 
    "ArchitecturalLayer",
    "validate_agent_architecture",
    "validate_agent_communication",
    "create_architecture_validator"
]
