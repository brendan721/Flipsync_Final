"""
FlipSync 4+1 Architecture Boundaries Enforcement
===============================================

Enforces clear separation between autonomous agents and conversational interface
to maintain the 85% autonomous, 15% Gemini architecture.

Architecture:
- 4 Autonomous Agents: Market, Content, Executive, Logistics
- 1 Conversational Interface: StrategicChatService
"""

from enum import Enum
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class ArchitecturalLayer(str, Enum):
    """Architectural layers in the 4+1 system."""
    
    AUTONOMOUS = "autonomous"
    CONVERSATIONAL = "conversational"
    UNKNOWN = "unknown"


class ArchitecturalBoundaries:
    """Enforce 4+1 architecture separation."""
    
    # Core 4 Autonomous Agents
    AUTONOMOUS_AGENTS = {
        "market_autonomous_agent": {
            "type": "autonomous",
            "capabilities": ["pricing", "inventory", "market_analysis", "competitive_analysis"],
            "dependencies": ["database", "decision_pipeline"],
            "forbidden_dependencies": ["llm_client", "chat_service"]
        },
        "content_autonomous_agent": {
            "type": "autonomous", 
            "capabilities": ["content_generation", "seo", "marketing", "optimization"],
            "dependencies": ["database", "decision_pipeline"],
            "forbidden_dependencies": ["llm_client", "chat_service"]
        },
        "executive_autonomous_agent": {
            "type": "autonomous",
            "capabilities": ["strategy", "coordination", "decisions", "oversight"],
            "dependencies": ["database", "decision_pipeline", "coordination"],
            "forbidden_dependencies": ["llm_client", "chat_service"]
        },
        "logistics_autonomous_agent": {
            "type": "autonomous",
            "capabilities": ["shipping", "fulfillment", "tracking", "inventory_management"],
            "dependencies": ["database", "decision_pipeline"],
            "forbidden_dependencies": ["llm_client", "chat_service"]
        }
    }
    
    # Automation Agents (Part of Autonomous Layer)
    AUTOMATION_AGENTS = {
        "auto_pricing_autonomous_agent": {
            "type": "autonomous",
            "capabilities": ["pricing_optimization", "algorithmic_pricing"],
            "dependencies": ["database", "decision_pipeline"],
            "forbidden_dependencies": ["llm_client", "chat_service"]
        },
        "auto_inventory_autonomous_agent": {
            "type": "autonomous",
            "capabilities": ["inventory_optimization", "reorder_analysis"],
            "dependencies": ["database", "decision_pipeline"],
            "forbidden_dependencies": ["llm_client", "chat_service"]
        },
        "auto_listing_autonomous_agent": {
            "type": "autonomous",
            "capabilities": ["listing_generation", "content_optimization"],
            "dependencies": ["database", "decision_pipeline"],
            "forbidden_dependencies": ["llm_client", "chat_service"]
        }
    }
    
    # Single Conversational Interface
    CONVERSATIONAL_INTERFACE = {
        "strategic_chat_service": {
            "type": "conversational",
            "capabilities": ["user_communication", "intent_analysis", "strategic_routing"],
            "dependencies": ["gemini_client", "agent_communication_protocol"],
            "forbidden_dependencies": ["direct_autonomous_agent_instantiation"]
        }
    }
    
    @classmethod
    def get_all_agents(cls) -> Dict[str, Dict]:
        """Get all registered agents in the 4+1 architecture."""
        all_agents = {}
        all_agents.update(cls.AUTONOMOUS_AGENTS)
        all_agents.update(cls.AUTOMATION_AGENTS)
        all_agents.update(cls.CONVERSATIONAL_INTERFACE)
        return all_agents
    
    @classmethod
    def validate_agent_type(cls, agent_id: str) -> ArchitecturalLayer:
        """Validate agent belongs to correct architectural layer."""
        all_agents = cls.get_all_agents()
        
        if agent_id in all_agents:
            agent_type = all_agents[agent_id]["type"]
            if agent_type == "autonomous":
                return ArchitecturalLayer.AUTONOMOUS
            elif agent_type == "conversational":
                return ArchitecturalLayer.CONVERSATIONAL
        
        logger.warning(f"Agent {agent_id} not found in 4+1 architecture registry")
        return ArchitecturalLayer.UNKNOWN
    
    @classmethod
    def get_agent_capabilities(cls, agent_id: str) -> List[str]:
        """Get capabilities for a specific agent."""
        all_agents = cls.get_all_agents()
        return all_agents.get(agent_id, {}).get("capabilities", [])
    
    @classmethod
    def get_allowed_dependencies(cls, agent_id: str) -> List[str]:
        """Get allowed dependencies for a specific agent."""
        all_agents = cls.get_all_agents()
        return all_agents.get(agent_id, {}).get("dependencies", [])
    
    @classmethod
    def get_forbidden_dependencies(cls, agent_id: str) -> List[str]:
        """Get forbidden dependencies for a specific agent."""
        all_agents = cls.get_all_agents()
        return all_agents.get(agent_id, {}).get("forbidden_dependencies", [])
    
    @classmethod
    def validate_dependency(cls, agent_id: str, dependency: str) -> bool:
        """Validate if a dependency is allowed for an agent."""
        forbidden = cls.get_forbidden_dependencies(agent_id)
        
        # Check for forbidden patterns
        for forbidden_pattern in forbidden:
            if forbidden_pattern.lower() in dependency.lower():
                logger.error(f"Forbidden dependency detected: {agent_id} -> {dependency}")
                return False
        
        return True
    
    @classmethod
    def validate_cross_layer_communication(cls, sender_agent: str, recipient_agent: str) -> bool:
        """Validate cross-layer communication follows 4+1 architecture rules."""
        sender_layer = cls.validate_agent_type(sender_agent)
        recipient_layer = cls.validate_agent_type(recipient_agent)
        
        # Autonomous agents can communicate with each other
        if sender_layer == ArchitecturalLayer.AUTONOMOUS and recipient_layer == ArchitecturalLayer.AUTONOMOUS:
            return True
        
        # Conversational interface can communicate with autonomous agents
        if sender_layer == ArchitecturalLayer.CONVERSATIONAL and recipient_layer == ArchitecturalLayer.AUTONOMOUS:
            return True
        
        # Autonomous agents can respond to conversational interface
        if sender_layer == ArchitecturalLayer.AUTONOMOUS and recipient_layer == ArchitecturalLayer.CONVERSATIONAL:
            return True
        
        # Conversational to conversational should be rare but allowed
        if sender_layer == ArchitecturalLayer.CONVERSATIONAL and recipient_layer == ArchitecturalLayer.CONVERSATIONAL:
            logger.warning(f"Conversational-to-conversational communication: {sender_agent} -> {recipient_agent}")
            return True
        
        logger.error(f"Invalid cross-layer communication: {sender_agent} ({sender_layer}) -> {recipient_agent} ({recipient_layer})")
        return False
    
    @classmethod
    def get_autonomous_agents(cls) -> List[str]:
        """Get list of all autonomous agent IDs."""
        autonomous_agents = []
        autonomous_agents.extend(cls.AUTONOMOUS_AGENTS.keys())
        autonomous_agents.extend(cls.AUTOMATION_AGENTS.keys())
        return autonomous_agents
    
    @classmethod
    def get_conversational_agents(cls) -> List[str]:
        """Get list of all conversational agent IDs."""
        return list(cls.CONVERSATIONAL_INTERFACE.keys())
    
    @classmethod
    def enforce_architecture_compliance(cls, agent_id: str, dependencies: List[str]) -> Dict[str, any]:
        """Enforce architecture compliance for an agent."""
        compliance_report = {
            "agent_id": agent_id,
            "layer": cls.validate_agent_type(agent_id).value,
            "compliant": True,
            "violations": [],
            "warnings": []
        }
        
        # Check dependencies
        for dependency in dependencies:
            if not cls.validate_dependency(agent_id, dependency):
                compliance_report["compliant"] = False
                compliance_report["violations"].append(f"Forbidden dependency: {dependency}")
        
        # Check if agent is registered
        if cls.validate_agent_type(agent_id) == ArchitecturalLayer.UNKNOWN:
            compliance_report["compliant"] = False
            compliance_report["violations"].append(f"Agent not registered in 4+1 architecture")
        
        return compliance_report


class ArchitectureValidator:
    """Validates system compliance with 4+1 architecture."""
    
    def __init__(self):
        self.boundaries = ArchitecturalBoundaries()
    
    def validate_system_architecture(self) -> Dict[str, any]:
        """Validate entire system architecture compliance."""
        validation_report = {
            "compliant": True,
            "autonomous_agents": len(self.boundaries.get_autonomous_agents()),
            "conversational_agents": len(self.boundaries.get_conversational_agents()),
            "total_agents": len(self.boundaries.get_all_agents()),
            "violations": [],
            "warnings": [],
            "architecture_summary": {
                "autonomous_layer": self.boundaries.get_autonomous_agents(),
                "conversational_layer": self.boundaries.get_conversational_agents()
            }
        }
        
        # Validate 4+1 structure
        autonomous_count = len(self.boundaries.get_autonomous_agents())
        conversational_count = len(self.boundaries.get_conversational_agents())
        
        if autonomous_count < 4:
            validation_report["compliant"] = False
            validation_report["violations"].append(f"Insufficient autonomous agents: {autonomous_count}/4+ required")
        
        if conversational_count != 1:
            validation_report["compliant"] = False
            validation_report["violations"].append(f"Invalid conversational interface count: {conversational_count}/1 required")
        
        return validation_report
    
    def generate_architecture_diagram(self) -> str:
        """Generate text-based architecture diagram."""
        autonomous_agents = self.boundaries.get_autonomous_agents()
        conversational_agents = self.boundaries.get_conversational_agents()
        
        diagram = """
FlipSync 4+1 Architecture
========================

Autonomous Layer (85% of processing):
"""
        for agent in autonomous_agents:
            capabilities = self.boundaries.get_agent_capabilities(agent)
            diagram += f"  ├─ {agent}\n"
            diagram += f"  │  └─ Capabilities: {', '.join(capabilities[:3])}{'...' if len(capabilities) > 3 else ''}\n"
        
        diagram += """
Conversational Layer (15% strategic Gemini):
"""
        for agent in conversational_agents:
            capabilities = self.boundaries.get_agent_capabilities(agent)
            diagram += f"  └─ {agent}\n"
            diagram += f"     └─ Capabilities: {', '.join(capabilities)}\n"
        
        return diagram


# Factory function for easy access
def create_architecture_validator() -> ArchitectureValidator:
    """Create architecture validator instance."""
    return ArchitectureValidator()


# Convenience functions
def validate_agent_architecture(agent_id: str, dependencies: List[str] = None) -> Dict[str, any]:
    """Validate single agent architecture compliance."""
    if dependencies is None:
        dependencies = []
    return ArchitecturalBoundaries.enforce_architecture_compliance(agent_id, dependencies)


def validate_agent_communication(sender: str, recipient: str) -> bool:
    """Validate agent-to-agent communication follows architecture rules."""
    return ArchitecturalBoundaries.validate_cross_layer_communication(sender, recipient)
