"""Compatibility module for content agent service."""

from fs_agt_clean.core.config import get_settings
from fs_agt_clean.core.monitoring.log_manager import LogManager
from fs_agt_clean.services.agents.content.content_agent_service import (
    ContentUnifiedAgentService,
)
from fs_agt_clean.services.llm.ollama_service import OllamaLLMService


async def get_content_agent_service() -> ContentUnifiedAgentService:
    """Get the content agent service instance.

    Returns:
        ContentUnifiedAgentService: Content agent service instance
    """
    config_manager = get_config_manager()
    log_manager = LogManager()

    # Initialize LLM service if available
    llm_service = None
    try:
        llm_service = OllamaLLMService(config_manager)
    except Exception:
        # If LLM service is not available, continue without it
        pass

    service = ContentUnifiedAgentService(
        config=config_manager,
        log_manager=log_manager,
        llm_service=llm_service,
    )

    await service.start()
    return service
