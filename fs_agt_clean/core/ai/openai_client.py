"""
Legacy OpenAI Client - DISABLED for 4+1 Architecture Compliance
===============================================================

This file has been disabled to maintain 4+1 architecture compliance.
All LLM functionality is now handled by StrategicGeminiService.

For any LLM needs, use:
from fs_agt_clean.core.ai.strategic_gemini_service import StrategicGeminiService
"""

# Redirect imports to StrategicGeminiService
from fs_agt_clean.core.ai.strategic_gemini_service import StrategicGeminiService

# Legacy compatibility - redirect to StrategicGeminiService
FlipSyncOpenAIClient = StrategicGeminiService
OpenAIConfig = dict  # Simple dict for config
TaskComplexity = str  # Simple string for complexity

def create_openai_client(*args, **kwargs):
    """Legacy compatibility - returns StrategicGeminiService."""
    return StrategicGeminiService(daily_budget=10.0)
