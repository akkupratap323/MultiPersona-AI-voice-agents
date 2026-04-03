"""
A2UI (Agent-to-UI) Service for Nester AI Voice Assistant

This module provides dynamic visual UI generation based on user queries.
It uses a 3-tier template selection system:

- Tier 1: Explicit template requests (user specifies template type)
- Tier 2: Semantic/keyword-based template selection (auto-detect intent)
- Tier 3: Fallback to simple-card for unmatched queries

Integration with Voice Assistant:
- A2UIRAGService: Full pipeline with LightRAG integration (recommended)
- A2UIGenerator: Local template filling from LLM text (fallback if LightRAG fails)
- Works alongside emotion detection and TTS

Pipeline Flow (AgenticUICatalog Architecture):
1. User query comes in
2. Orchestrator detects tier and selects template type
3. Template structure loaded from library
4. Query + Template + Instructions → LightRAG
5. LightRAG fills template from knowledge base
6. Filled A2UI + Text → Frontend rendering
"""

from loguru import logger

# Log A2UI module initialization
logger.info("=" * 60)
logger.info("🎨 A2UI SERVICE MODULE LOADING...")
logger.info("=" * 60)

from .orchestrator import A2UIOrchestrator, detect_tier, get_tier_metadata
logger.info("✅ A2UI Orchestrator loaded (3-tier template selection)")

from .template_library import (
    TEMPLATE_LIBRARY,
    get_template_from_library,
    list_available_templates,
    get_template_catalog
)
logger.info(f"✅ A2UI Template Library loaded ({len(TEMPLATE_LIBRARY)} templates available)")

from .a2ui_generator import A2UIGenerator
logger.info("✅ A2UI Generator loaded (LLM response → visual cards)")

from .a2ui_rag_service import A2UIRAGService, get_a2ui_rag_service
logger.info("✅ A2UI RAG Service loaded (LightRAG + A2UI integration)")

logger.info("=" * 60)
logger.info("🎨 A2UI SERVICE MODULE READY!")
logger.info("=" * 60)

__all__ = [
    # Orchestrator
    "A2UIOrchestrator",
    "detect_tier",
    "get_tier_metadata",
    # Template Library
    "TEMPLATE_LIBRARY",
    "get_template_from_library",
    "list_available_templates",
    "get_template_catalog",
    # Generator (local fallback)
    "A2UIGenerator",
    # RAG Integration (full pipeline)
    "A2UIRAGService",
    "get_a2ui_rag_service",
]
