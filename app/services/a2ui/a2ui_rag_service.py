"""
A2UI RAG Service - Integrates A2UI generation with LightRAG retrieval.

This service follows the AgenticUICatalog architecture:
1. User query → Orchestrator → Detect tier, select template type
2. Query + Template + Instructions → LightRAG → Filled A2UI + Text response
3. Text + Filled A2UI → Frontend for rendering

Flow (AgenticUICatalog Architecture):
1. User query comes in
2. Match template with user query using tier detection
3. Send query + template + instructions to LightRAG
4. LightRAG fills the template and returns both text and filled A2UI
5. Return filled A2UI + text to frontend

Note: LightRAG handles BOTH knowledge retrieval AND template filling.
"""

from typing import Any, Dict, Optional
from loguru import logger

from .orchestrator import detect_tier, get_tier_metadata
from .template_library import get_template_from_library, TEMPLATE_LIBRARY
from ..rag import LightRAGService, A2UIResponse, BaseRAGService


# Template-specific instructions for LightRAG (matching AgenticUICatalog format)
TEMPLATE_INSTRUCTIONS = {
    "template-grid": """
Generate a template-grid A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "template-grid",
    "props": {
      "title": "Grid Title",
      "templates": [
        {
          "name": "Item Name",
          "description": "Item description",
          "category": "Category Name",
          "tags": ["tag1", "tag2"]
        }
      ],
      "columns": 3,
      "showSearch": true,
      "showCount": true
    }
  }
}

Extract items from the context and fill the templates array.
""",

    "service-hover-reveal": """
Generate a service-hover-reveal A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "service-hover-reveal",
    "props": {
      "title": "Services Title",
      "services": [
        {
          "name": "Service Name",
          "description": "Brief description of the service"
        }
      ]
    }
  }
}

Extract service information from the context and fill the template.
""",

    "contact-card": """
Generate a contact-card A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "contact-card",
    "props": {
      "title": "Contact Information",
      "contacts": [
        {
          "type": "email",
          "value": "email@example.com",
          "description": "General inquiries"
        },
        {
          "type": "phone",
          "value": "+1 234 567 8900",
          "description": "Call us"
        },
        {
          "type": "website",
          "value": "https://example.com"
        }
      ]
    }
  }
}

Extract contact information from the context and fill the contacts array.
""",

    "timeline": """
Generate a timeline A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "timeline",
    "props": {
      "title": "Timeline Title",
      "events": [
        {
          "year": "2020",
          "title": "Event Title",
          "description": "Event description"
        }
      ]
    }
  }
}

Extract chronological events from the context and fill the events array.
""",

    "team-flip-cards": """
Generate a team-flip-cards A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "team-flip-cards",
    "props": {
      "title": "Team Title",
      "members": [
        {
          "name": "Person Name",
          "role": "Role/Title",
          "bio": "Brief bio",
          "image": "https://example.com/photo.jpg",
          "email": "person@example.com",
          "linkedin": "https://linkedin.com/in/username"
        }
      ]
    }
  }
}

Extract team member information from the context and fill the members array.
IMPORTANT: Include 'image' (photo URL), 'email', and 'linkedin' fields if available in the context.
""",

    "faq-accordion": """
Generate a faq-accordion A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "faq-accordion",
    "props": {
      "title": "Frequently Asked Questions",
      "faqs": [
        {
          "question": "Question text?",
          "answer": "Answer text"
        }
      ]
    }
  }
}

Extract Q&A pairs from the context and fill the faqs array.
""",

    "comparison-chart": """
Generate a comparison-chart A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "comparison-chart",
    "props": {
      "title": "Comparison Title",
      "items": [
        {
          "name": "Item Name",
          "features": [
            {"feature": "Feature Name", "value": "Feature Value"}
          ],
          "recommended": false
        }
      ]
    }
  }
}

Extract items to compare from the context and fill the items array.
""",

    "stats-flow-layout": """
Generate a stats-flow-layout A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "stats-flow-layout",
    "props": {
      "title": "Statistics Title",
      "topStats": [
        {"label": "Metric Name", "value": "100+"}
      ],
      "bottomStats": [
        {"label": "Secondary Metric", "value": "50"}
      ]
    }
  }
}

Extract statistics and metrics from the context and fill the stats arrays.
""",

    "magazine-hero": """
Generate a magazine-hero A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "magazine-hero",
    "props": {
      "title": "Main Title",
      "subtitle": "Subtitle text",
      "content": "Main content text describing the topic in detail.",
      "pullQuote": "Notable quote if available"
    }
  }
}

Extract the main title, subtitle, and content from the context.
""",

    "image-gallery": """
Generate an image-gallery A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "image-gallery",
    "props": {
      "title": "Gallery Title",
      "images": [
        {
          "url": "https://example.com/image.jpg",
          "caption": "Image caption",
          "alt": "Alt text"
        }
      ]
    }
  }
}

Extract image information from the context and fill the images array.
""",

    "video-gallery": """
Generate a video-gallery A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "video-gallery",
    "props": {
      "title": "Video Gallery Title",
      "videos": [
        {
          "url": "https://youtube.com/watch?v=...",
          "title": "Video Title",
          "description": "Video description"
        }
      ]
    }
  }
}

Extract video information from the context and fill the videos array.
""",

    "simple-card": """
Generate a simple-card A2UI template with the following structure:
{
  "version": "1.0",
  "root": {
    "type": "simple-card",
    "props": {
      "title": "Card Title",
      "content": "Card content text",
      "icon": "info"
    }
  }
}

Extract a title and summary content from the context.
""",
}


def get_template_instructions(template_type: str) -> str:
    """
    Get filling instructions for a specific template type.
    Matches the AgenticUICatalog prompt format for LightRAG.

    Args:
        template_type: Type of template to get instructions for

    Returns:
        Instructions string for the LLM
    """
    base_instructions = TEMPLATE_INSTRUCTIONS.get(template_type, f"""
Generate an A2UI template of type "{template_type}".
Analyze the context and extract relevant information to fill the template.
""")

    return f"""You are an A2UI generator. Your task is to create a structured, filled A2UI JSON template based on the user's query and the provided context.

{base_instructions}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no code blocks, no explanatory text
2. Extract REAL data from the context - do not use placeholders like "{{ PLACEHOLDER }}"
3. If context is insufficient, use empty strings "" or empty arrays [] - NEVER use placeholders
4. Ensure all arrays (services, templates, members, etc.) are properly populated with extracted data
5. Keep descriptions concise (under 250 characters)

Return the JSON directly:"""


class A2UIRAGService:
    """
    Service that combines A2UI template selection with LightRAG retrieval.

    This follows the AgenticUICatalog pipeline architecture:
    - Query analysis → Template selection → Query+Template → LightRAG → Filled A2UI

    Attributes:
        rag_service: LightRAG service instance for knowledge retrieval + template filling
        enabled: Whether A2UI generation is enabled
        tier_mode: Template selection mode (auto, semantic, explicit)
        min_confidence: Minimum confidence for template selection
    """

    def __init__(
        self,
        rag_service: BaseRAGService,
        enabled: bool = True,
        tier_mode: str = "auto",
        min_confidence: float = 0.5,
    ):
        """
        Initialize the A2UI RAG service.

        Args:
            rag_service: RAG service instance (should be LightRAGService for full A2UI support)
            enabled: Enable A2UI generation
            tier_mode: Template selection mode
            min_confidence: Minimum confidence threshold for template selection
        """
        self.rag_service = rag_service
        self.enabled = enabled
        self.tier_mode = tier_mode
        self.min_confidence = min_confidence
        self._has_a2ui_support = isinstance(rag_service, LightRAGService)

        logger.info("=" * 60)
        logger.info("🎨 A2UI RAG SERVICE INITIALIZED")
        logger.info(f"   Enabled: {enabled}")
        logger.info(f"   Tier mode: {tier_mode}")
        logger.info(f"   Min confidence: {min_confidence}")
        logger.info(f"   RAG service type: {type(rag_service).__name__}")
        logger.info(f"   Full A2UI support: {self._has_a2ui_support}")
        logger.info("=" * 60)

    async def query(
        self,
        query: str,
        custom_template: Optional[Dict[str, Any]] = None,
        force_text_only: bool = False,
    ) -> A2UIResponse:
        """
        Query the knowledge base with automatic A2UI template selection and filling.

        This implements the AgenticUICatalog pipeline:
        1. User query comes in
        2. Match template with user query using tier detection
        3. Send query + template + instructions to LightRAG
        4. LightRAG fills the template and returns both text and filled A2UI

        Args:
            query: User's question
            custom_template: Optional custom template (bypasses auto-selection)
            force_text_only: If True, skip A2UI generation and return text only

        Returns:
            A2UIResponse with text and optionally filled A2UI template
        """
        import time
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("🚀 A2UI RAG QUERY STARTING")
        logger.info(f"   Query: '{query[:60]}{'...' if len(query) > 60 else ''}'")
        logger.info(f"   Enabled: {self.enabled}")
        logger.info(f"   Force text only: {force_text_only}")
        logger.info(f"   Custom template: {custom_template is not None}")
        logger.info("=" * 60)

        # If A2UI is disabled or text-only requested, just return text
        if not self.enabled or force_text_only:
            logger.info("📝 A2UI disabled - returning text only")
            text = await self.rag_service.get_response(query)
            return A2UIResponse(text=text)

        # Step 1: Detect tier and select template type
        logger.info("🎯 Step 1: Detecting tier and selecting template...")

        # Determine if semantic should be used based on tier_mode config
        use_semantic = self.tier_mode in ["auto", "semantic"]
        logger.info(f"   Using semantic matching: {use_semantic} (tier_mode={self.tier_mode})")

        tier_info = detect_tier(query, custom_template, use_semantic=use_semantic)
        template_type = tier_info["template_type"]
        logger.info(f"   Tier detected: {tier_info['tier_name']}")
        logger.info(f"   Template type: {template_type}")
        if tier_info.get('matched_keyword'):
            logger.info(f"   Matched keyword: '{tier_info['matched_keyword']}'")

        # Step 2: Get template structure from library
        logger.info("📋 Step 2: Getting template structure from library...")
        template = get_template_from_library(template_type)
        if template:
            logger.info(f"   ✅ Template '{template_type}' loaded from library")
        else:
            logger.warning(f"   ⚠️ Template '{template_type}' not found, using simple-card fallback")
            template = get_template_from_library("simple-card")
            template_type = "simple-card"

        # Step 3: Get template-specific instructions
        logger.info("📝 Step 3: Building template instructions...")
        instructions = get_template_instructions(template_type)

        # Step 4: Send query + template + instructions to LightRAG
        logger.info("📡 Step 4: Sending to LightRAG (query + template + instructions)...")

        if self._has_a2ui_support:
            # Use the full A2UI-aware method
            a2ui_response = await self.rag_service.get_response_with_a2ui(
                query=query,
                a2ui_template=template,
                template_instructions=instructions,
            )

            # Add tier metadata
            if a2ui_response.a2ui:
                a2ui_response.a2ui["_metadata"] = get_tier_metadata(tier_info)

            # Update tier info from our detection
            a2ui_response.tier = tier_info["tier"]
            a2ui_response.template_type = template_type

        else:
            # Fallback for non-LightRAG services: get text only
            logger.warning("⚠️ RAG service doesn't support A2UI - falling back to text only")
            text_response = await self.rag_service.get_response(query)
            a2ui_response = A2UIResponse(
                text=text_response,
                tier=tier_info["tier"],
                template_type=template_type,
            )

        elapsed_ms = (time.time() - start_time) * 1000
        a2ui_response.query_time_ms = elapsed_ms

        # Check if response is an error
        if self._is_error_response(a2ui_response.text):
            logger.warning("⚠️ LightRAG returned error text; clearing A2UI")
            a2ui_response.a2ui = None

        # Log result
        if a2ui_response.a2ui:
            filled_type = a2ui_response.a2ui.get("root", {}).get("type", "unknown")
            props = a2ui_response.a2ui.get("root", {}).get("props", {})
            logger.info(f"✅ A2UI RAG query complete in {elapsed_ms:.1f}ms")
            logger.info(f"   Template: {filled_type}")
            logger.info(f"   Tier: {tier_info['tier']}")

            # Log array sizes
            for key in ["templates", "services", "contacts", "events", "faqs", "members", "items"]:
                if key in props and isinstance(props[key], list):
                    logger.info(f"   {key}: {len(props[key])} items")
        else:
            logger.info(f"⚠️ A2UI query complete (text only) in {elapsed_ms:.1f}ms")

        return a2ui_response

    def _is_error_response(self, text: str) -> bool:
        """Detect error responses from RAG so we don't render A2UI."""
        if not text:
            return True
        normalized = text.strip().lower()
        return (
            "i encountered an error while searching the knowledge base" in normalized
            or "i encountered an error:" in normalized
            or "i'm having trouble accessing the knowledge base" in normalized
            or normalized.startswith("i encountered an error")
            or normalized.startswith("i apologize, but i encountered an error")
        )

    def get_available_templates(self) -> Dict[str, Any]:
        """
        Get list of available template types.

        Returns:
            Dictionary of available templates and their descriptions
        """
        return {
            name: {
                "type": template.get("root", {}).get("type", name),
                "version": template.get("version", "1.0"),
            }
            for name, template in TEMPLATE_LIBRARY.items()
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get service status.

        Returns:
            Status dictionary
        """
        return {
            "enabled": self.enabled,
            "tier_mode": self.tier_mode,
            "min_confidence": self.min_confidence,
            "rag_type": type(self.rag_service).__name__,
            "has_a2ui_support": self._has_a2ui_support,
            "available_templates": list(TEMPLATE_LIBRARY.keys()),
        }


# Singleton instance
_a2ui_rag_service: Optional[A2UIRAGService] = None


def get_a2ui_rag_service(
    rag_service: Optional[BaseRAGService] = None,
    enabled: bool = True,
    tier_mode: str = "auto",
    min_confidence: float = 0.5,
) -> A2UIRAGService:
    """
    Get or create the A2UI RAG service singleton.

    Args:
        rag_service: RAG service instance (required on first call)
        enabled: Enable A2UI generation
        tier_mode: Template selection mode
        min_confidence: Minimum confidence threshold

    Returns:
        A2UIRAGService instance
    """
    global _a2ui_rag_service

    if _a2ui_rag_service is None:
        if rag_service is None:
            raise ValueError("rag_service is required on first call to get_a2ui_rag_service")

        _a2ui_rag_service = A2UIRAGService(
            rag_service=rag_service,
            enabled=enabled,
            tier_mode=tier_mode,
            min_confidence=min_confidence,
        )

    return _a2ui_rag_service
