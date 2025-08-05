
"""
CrossAgentLearningCoordinator Factory
====================================

Factory function to properly initialize CrossAgentLearningCoordinator
with required parameters.
"""

from fs_agt_clean.core.coordination.cross_agent_learning_coordinator import CrossAgentLearningCoordinator
from fs_agt_clean.core.db.optimized_database import get_initialized_database
from fs_agt_clean.core.coordination.multi_agent_coordinator import MultiAgentCoordinator

async def create_cross_agent_learning_coordinator(coordinator_id: str = "main_learning_coordinator"):
    """Create properly initialized CrossAgentLearningCoordinator."""
    
    # Get required dependencies
    database = await get_initialized_database()
    multi_agent_coordinator = MultiAgentCoordinator()
    
    # Create coordinator with proper parameters
    coordinator = CrossAgentLearningCoordinator(
        coordinator_id=coordinator_id,
        database=database,
        multi_agent_coordinator=multi_agent_coordinator
    )
    
    return coordinator

async def test_cross_agent_learning_coordinator():
    """Test CrossAgentLearningCoordinator functionality."""
    try:
        coordinator = await create_cross_agent_learning_coordinator()
        
        # Test basic functionality
        test_result = {
            'coordinator_created': True,
            'knowledge_sharing_available': hasattr(coordinator, 'share_knowledge'),
            'learning_enabled': hasattr(coordinator, 'process_learning')
        }
        
        return test_result
        
    except Exception as e:
        return {'error': str(e), 'coordinator_created': False}
