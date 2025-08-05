"""
FlipSync Runtime Architecture Boundary Enforcement
=================================================

Implements runtime validation to prevent fallback to in-memory components
and enforce the 4+1 architecture during agent initialization and operation.

Key Features:
- Prevents InMemory* component instantiation at runtime
- Validates database-backed components are used
- Enforces LLM dependency restrictions for autonomous agents
- Validates 4+1 architecture compliance during operation
"""

import logging
import time
from typing import Dict, Any, List, Optional, Set
from enum import Enum

from fs_agt_clean.core.architecture.boundaries import (
    ArchitecturalBoundaries,
    ArchitectureValidator,
    ArchitecturalLayer
)

logger = logging.getLogger(__name__)


class RuntimeViolationType(str, Enum):
    """Types of runtime architecture violations."""
    
    INMEMORY_COMPONENT_USAGE = "inmemory_component_usage"
    LLM_DEPENDENCY_VIOLATION = "llm_dependency_violation"
    ARCHITECTURE_BOUNDARY_VIOLATION = "architecture_boundary_violation"
    DATABASE_FALLBACK_DETECTED = "database_fallback_detected"
    FORBIDDEN_DEPENDENCY_INJECTION = "forbidden_dependency_injection"


class RuntimeArchitectureValidator:
    """Runtime validator for FlipSync 4+1 architecture compliance."""
    
    def __init__(self):
        self.boundaries = ArchitecturalBoundaries()
        self.architecture_validator = ArchitectureValidator()
        self.violation_log: List[Dict[str, Any]] = []
        self.monitored_agents: Set[str] = set()
        
        # Forbidden component patterns for autonomous agents
        self.forbidden_inmemory_components = {
            'InMemoryDecisionMaker',
            'InMemoryLearningEngine', 
            'InMemoryDecisionTracker',
            'InMemoryFeedbackProcessor',
            'InMemoryPolicyOptimizer'
        }
        
        # Forbidden LLM patterns for autonomous agents
        self.forbidden_llm_patterns = {
            'openai_client',
            'HybridLLMAdapter',
            'SimpleLLMClient',
            'llm_client',
            'create_smart_client',
            'create_business_client',
            'create_complex_agent_client'
        }
        
        logger.info("RuntimeArchitectureValidator initialized for 4+1 architecture enforcement")
    
    def validate_agent_initialization(self, agent_id: str, agent_instance: Any) -> Dict[str, Any]:
        """Validate agent initialization complies with architecture boundaries."""
        validation_start = time.perf_counter()
        
        validation_result = {
            'agent_id': agent_id,
            'compliant': True,
            'violations': [],
            'warnings': [],
            'validation_time_ms': 0,
            'architecture_layer': None,
            'component_analysis': {}
        }
        
        try:
            # Determine agent's architectural layer
            agent_layer = self.boundaries.validate_agent_type(agent_id)
            validation_result['architecture_layer'] = agent_layer.value
            
            # Add to monitored agents
            self.monitored_agents.add(agent_id)
            
            # Validate based on architectural layer
            if agent_layer == ArchitecturalLayer.AUTONOMOUS:
                self._validate_autonomous_agent(agent_instance, validation_result)
            elif agent_layer == ArchitecturalLayer.CONVERSATIONAL:
                self._validate_conversational_agent(agent_instance, validation_result)
            else:
                validation_result['violations'].append(
                    f"Agent {agent_id} not registered in 4+1 architecture"
                )
                validation_result['compliant'] = False
            
            # Log violations
            if validation_result['violations']:
                self._log_violations(agent_id, validation_result['violations'])
            
            validation_time = (time.perf_counter() - validation_start) * 1000
            validation_result['validation_time_ms'] = validation_time
            
            logger.info(
                f"Runtime validation for {agent_id}: "
                f"{'✅ COMPLIANT' if validation_result['compliant'] else '❌ VIOLATIONS'} "
                f"({validation_time:.1f}ms)"
            )
            
        except Exception as e:
            logger.error(f"Runtime validation error for {agent_id}: {e}")
            validation_result['compliant'] = False
            validation_result['violations'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _validate_autonomous_agent(self, agent_instance: Any, validation_result: Dict[str, Any]):
        """Validate autonomous agent compliance with zero LLM dependencies."""
        
        # Check for forbidden InMemory* components
        self._check_inmemory_components(agent_instance, validation_result)
        
        # Check for forbidden LLM dependencies
        self._check_llm_dependencies(agent_instance, validation_result)
        
        # Validate database-backed components
        self._validate_database_components(agent_instance, validation_result)
        
        # Validate decision pipeline usage
        self._validate_decision_pipeline(agent_instance, validation_result)
    
    def _validate_conversational_agent(self, agent_instance: Any, validation_result: Dict[str, Any]):
        """Validate conversational agent compliance with Gemini-only usage."""
        
        # Conversational agents are allowed LLM usage (Gemini preferred)
        validation_result['warnings'].append(
            "Conversational agent - LLM usage permitted (prefer Gemini over OpenAI)"
        )
        
        # Check for direct autonomous agent instantiation (forbidden)
        self._check_direct_autonomous_instantiation(agent_instance, validation_result)
    
    def _check_inmemory_components(self, agent_instance: Any, validation_result: Dict[str, Any]):
        """Check for forbidden InMemory* component usage."""
        
        for attr_name in dir(agent_instance):
            if attr_name.startswith('_'):
                continue
                
            try:
                attr_value = getattr(agent_instance, attr_name)
                if attr_value is None:
                    continue
                
                # Check class name for InMemory patterns
                class_name = attr_value.__class__.__name__
                
                if any(forbidden in class_name for forbidden in self.forbidden_inmemory_components):
                    validation_result['violations'].append(
                        f"Forbidden InMemory component detected: {attr_name} -> {class_name}"
                    )
                    validation_result['compliant'] = False
                    
            except Exception:
                # Skip attributes that can't be accessed
                continue
    
    def _check_llm_dependencies(self, agent_instance: Any, validation_result: Dict[str, Any]):
        """Check for forbidden LLM dependencies in autonomous agents."""
        
        for attr_name in dir(agent_instance):
            if attr_name.startswith('_'):
                continue
                
            try:
                attr_value = getattr(agent_instance, attr_name)
                
                # Check for None values (acceptable - LLM dependency removed)
                if attr_value is None and any(pattern in attr_name for pattern in self.forbidden_llm_patterns):
                    validation_result['component_analysis'][attr_name] = "LLM dependency properly removed (None)"
                    continue
                
                if attr_value is None:
                    continue
                
                # Check class name and attribute name for LLM patterns
                class_name = attr_value.__class__.__name__
                
                if (any(pattern in attr_name for pattern in self.forbidden_llm_patterns) or
                    any(pattern in class_name for pattern in self.forbidden_llm_patterns)):
                    
                    validation_result['violations'].append(
                        f"Forbidden LLM dependency detected: {attr_name} -> {class_name}"
                    )
                    validation_result['compliant'] = False
                    
            except Exception:
                # Skip attributes that can't be accessed
                continue
    
    def _validate_database_components(self, agent_instance: Any, validation_result: Dict[str, Any]):
        """Validate that database-backed components are used."""
        
        required_database_components = [
            'decision_pipeline',
            'database',
            'decision_database'
        ]
        
        for component in required_database_components:
            if hasattr(agent_instance, component):
                component_value = getattr(agent_instance, component)
                if component_value is not None:
                    validation_result['component_analysis'][component] = f"Present: {component_value.__class__.__name__}"
                else:
                    validation_result['warnings'].append(f"Database component {component} is None")
            else:
                validation_result['warnings'].append(f"Database component {component} not found")
    
    def _validate_decision_pipeline(self, agent_instance: Any, validation_result: Dict[str, Any]):
        """Validate StandardDecisionPipeline usage."""
        
        if hasattr(agent_instance, 'decision_pipeline'):
            pipeline = getattr(agent_instance, 'decision_pipeline')
            if pipeline is not None:
                pipeline_class = pipeline.__class__.__name__
                if 'StandardDecisionPipeline' in pipeline_class:
                    validation_result['component_analysis']['decision_pipeline'] = f"✅ {pipeline_class}"
                else:
                    validation_result['warnings'].append(f"Non-standard decision pipeline: {pipeline_class}")
            else:
                validation_result['violations'].append("Decision pipeline is None")
                validation_result['compliant'] = False
        else:
            validation_result['violations'].append("Decision pipeline not found")
            validation_result['compliant'] = False
    
    def _check_direct_autonomous_instantiation(self, agent_instance: Any, validation_result: Dict[str, Any]):
        """Check for direct autonomous agent instantiation in conversational agents."""
        
        # This would require more sophisticated inspection
        # For now, just add a warning
        validation_result['warnings'].append(
            "Conversational agent should use agent communication protocol, not direct instantiation"
        )
    
    def _log_violations(self, agent_id: str, violations: List[str]):
        """Log architecture violations for monitoring."""
        
        violation_entry = {
            'timestamp': time.time(),
            'agent_id': agent_id,
            'violations': violations,
            'violation_count': len(violations)
        }
        
        self.violation_log.append(violation_entry)
        
        # Log each violation
        for violation in violations:
            logger.error(f"🚨 Architecture Violation [{agent_id}]: {violation}")
    
    def prevent_inmemory_fallback(self, component_type: str, agent_id: str) -> bool:
        """Prevent fallback to in-memory components at runtime."""
        
        if any(forbidden in component_type for forbidden in self.forbidden_inmemory_components):
            logger.error(
                f"🚨 RUNTIME BLOCK: Prevented {component_type} instantiation for {agent_id}"
            )
            
            # Log the violation
            self._log_violations(agent_id, [f"Attempted {component_type} instantiation blocked"])
            
            # Raise exception to prevent instantiation
            raise RuntimeError(
                f"Architecture violation: {component_type} is forbidden for autonomous agent {agent_id}. "
                f"Use database-backed components only."
            )
        
        return True
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        
        report = {
            'timestamp': time.time(),
            'monitored_agents': len(self.monitored_agents),
            'total_violations': len(self.violation_log),
            'agents_with_violations': len(set(v['agent_id'] for v in self.violation_log)),
            'violation_summary': {},
            'architecture_status': self.architecture_validator.validate_system_architecture(),
            'recent_violations': self.violation_log[-10:] if self.violation_log else []
        }
        
        # Summarize violation types
        for violation_entry in self.violation_log:
            agent_id = violation_entry['agent_id']
            if agent_id not in report['violation_summary']:
                report['violation_summary'][agent_id] = {
                    'violation_count': 0,
                    'violation_types': set()
                }
            
            report['violation_summary'][agent_id]['violation_count'] += violation_entry['violation_count']
            
            for violation in violation_entry['violations']:
                if 'InMemory' in violation:
                    report['violation_summary'][agent_id]['violation_types'].add('inmemory_component')
                elif 'LLM' in violation:
                    report['violation_summary'][agent_id]['violation_types'].add('llm_dependency')
                else:
                    report['violation_summary'][agent_id]['violation_types'].add('other')
        
        # Convert sets to lists for JSON serialization
        for agent_summary in report['violation_summary'].values():
            agent_summary['violation_types'] = list(agent_summary['violation_types'])
        
        return report


# Global runtime validator instance
_runtime_validator: Optional[RuntimeArchitectureValidator] = None


def get_runtime_validator() -> RuntimeArchitectureValidator:
    """Get or create global runtime validator instance."""
    global _runtime_validator
    if _runtime_validator is None:
        _runtime_validator = RuntimeArchitectureValidator()
    return _runtime_validator


def validate_agent_runtime_compliance(agent_id: str, agent_instance: Any) -> Dict[str, Any]:
    """Validate agent runtime compliance with 4+1 architecture."""
    validator = get_runtime_validator()
    return validator.validate_agent_initialization(agent_id, agent_instance)


def prevent_inmemory_component_usage(component_type: str, agent_id: str) -> bool:
    """Prevent in-memory component usage at runtime."""
    validator = get_runtime_validator()
    return validator.prevent_inmemory_fallback(component_type, agent_id)


def get_architecture_compliance_report() -> Dict[str, Any]:
    """Get comprehensive architecture compliance report."""
    validator = get_runtime_validator()
    return validator.get_compliance_report()
