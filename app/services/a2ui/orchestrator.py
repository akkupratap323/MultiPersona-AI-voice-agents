"""
A2UI Orchestrator - 3-Tier Template Selection System

This module implements the tier detection logic that selects appropriate
visual templates based on user queries.

TIER 1a: Custom Template (API Parameter)
   - Caller provides custom template via API
   - Highest priority, direct pass-through

TIER 1b: Explicit Template Request
   - User explicitly mentions a template type name
   - Examples: "show me a contact card", "use timeline template"

TIER 2: Semantic/Keyword Intent Understanding
   - Semantic: Uses sentence embeddings for intent understanding
   - Keyword: Falls back to pattern matching if semantic unavailable
   - Examples: "how can I contact you" → contact-card

TIER 2a: Critical Pattern Override
   - Strong pattern matches that bypass semantic/keyword priority
   - "what is X" / "who is X" → magazine-hero (for single-subject queries)
   - Contact patterns with multiple keywords → contact-card

TIER 3: Fallback to Magazine Hero
   - No pattern matches, use magazine-style content
"""

from typing import Optional, Dict, Any
from loguru import logger

# Try to import semantic selector (optional dependency)
try:
    from .semantic_selector import get_semantic_selector, is_semantic_available
    SEMANTIC_AVAILABLE = is_semantic_available()
except ImportError:
    SEMANTIC_AVAILABLE = False
    get_semantic_selector = None
    is_semantic_available = None


# Tier 1: Explicit template keywords (user requests specific template)
TIER1_TEMPLATE_KEYWORDS = {
    "contact-card": ["contact-card", "contact card", "show contact"],
    "template-grid": ["template-grid", "grid template", "show grid"],
    "timeline": ["timeline template", "show timeline", "timeline view"],
    "comparison-chart": ["comparison-chart", "comparison chart", "compare chart"],
    "stats-chart": ["stats-chart", "stats chart", "statistics chart"],
    "stats-flow-layout": ["stats-flow", "dashboard", "stats dashboard"],
    "service-hover-reveal": ["service-hover", "services list"],
    "team-flip-cards": ["team-flip", "team cards", "flip cards"],
    "image-gallery": ["image-gallery", "photo gallery", "show images"],
    "video-gallery": ["video-gallery", "show videos", "video list"],
    "faq-accordion": ["faq-accordion", "faq section", "show faq"],
    "magazine-hero": ["magazine-hero", "article view", "hero section"],
}

# Tier 2: Pattern-based template detection (content-type keywords)
# Priority: Higher number = higher priority (checked first / preferred over lower priority)
TEMPLATE_PATTERNS = {
    "contact": {
        "keywords": ["contact", "reach", "email", "phone", "address", "location", "office", "call us", "located", "where are you", "get in touch", "talk to someone"],
        "template_type": "contact-card",
        "description": "Contact information card",
        "priority": 90
    },
    "timeline": {
        "keywords": ["history", "milestone", "founded", "since", "timeline", "chronological", "roadmap", "journey", "began", "started"],
        "template_type": "timeline",
        "description": "Chronological timeline view",
        "priority": 80
    },
    "projects": {
        "keywords": ["project", "projects", "completed", "portfolio", "case study", "built", "work", "worked on",
                     "kahuna", "basepair", "squarex", "astha", "banky", "revops", "sarah", "intake coordinator",
                     "mentorship platform", "genomic", "conversations with data"],
        "template_type": "template-grid",
        "description": "Grid layout for project listings",
        "priority": 85
    },
    "products": {
        "keywords": ["product", "products", "offering", "solution", "item", "items"],
        "template_type": "template-grid",
        "description": "Product grid layout",
        "priority": 85
    },
    "services": {
        "keywords": ["service", "services", "provide", "offer", "what do you do", "capabilities", "expertise", "specialize", "specialization", "pillar"],
        "template_type": "service-hover-reveal",
        "description": "Service hover-reveal list",
        "priority": 85
    },
    "team": {
        "keywords": ["team", "member", "staff", "employee", "people", "who work", "founders", "who is",
                     "who are", "co-founder", "leadership", "ankur", "kunal", "shrey", "gaurav"],
        "template_type": "team-flip-cards",
        "description": "Team flip cards",
        "priority": 80
    },
    "comparison": {
        "keywords": ["compare", "comparison", "versus", "vs", "difference", "better than", "which is better"],
        "template_type": "comparison-chart",
        "description": "Comparison chart",
        "priority": 95  # High priority - comparison intent should override content type
    },
    "statistics": {
        "keywords": ["statistic", "metric", "number", "data", "analytics", "kpi", "revenue", "growth"],
        "template_type": "stats-flow-layout",
        "description": "Statistics dashboard",
        "priority": 75
    },
    "videos": {
        "keywords": ["video", "watch", "youtube", "vimeo", "clip", "recording", "demo", "webinar", "tutorial"],
        "template_type": "video-gallery",
        "description": "Video gallery display",
        "priority": 70
    },
    "images": {
        "keywords": ["image", "photo", "picture", "logo", "screenshot", "visual"],
        "template_type": "image-gallery",
        "description": "Image gallery display",
        "priority": 70
    },
    "faq": {
        "keywords": ["faq", "frequently asked", "questions", "q&a", "common questions", "what do people ask", "how do i", "can i"],
        "template_type": "faq-accordion",
        "description": "FAQ accordion",
        "priority": 80
    },
    "about": {
        "keywords": ["describe", "explain", "overview", "about the company", "about us"],
        "template_type": "magazine-hero",
        "description": "Magazine-style content",
        "priority": 50  # Low priority - only use when no specific content type matches
    }
}


class A2UIOrchestrator:
    """
    A2UI Orchestrator for template selection based on user queries.

    Provides multi-tier template selection (matching a2ui-chatbot-service):
    1a. Custom template (API parameter)
    1b. Explicit template requests (user mentions template name)
    2a. Critical pattern overrides (contact, "what is" queries)
    2b. Semantic intent understanding (sentence embeddings)
    2c. Keyword pattern matching (fallback)
    3. Fallback to magazine-hero
    """

    def __init__(self, use_semantic: bool = True):
        """
        Initialize the orchestrator.

        Args:
            use_semantic: Enable semantic matching (requires sentence-transformers)
                         Default: True (recommended for voice interfaces)
        """
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self._semantic_selector = None

        if self.use_semantic:
            try:
                self._semantic_selector = get_semantic_selector()
                if self._semantic_selector:
                    logger.info("✅ Semantic template selector initialized")
                else:
                    logger.warning("⚠️ Semantic selector returned None, using keyword matching only")
                    self.use_semantic = False
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize semantic selector: {e}")
                logger.warning("   Falling back to keyword matching only")
                self.use_semantic = False
        else:
            if use_semantic and not SEMANTIC_AVAILABLE:
                logger.warning("⚠️ sentence-transformers not installed, using keyword matching only")
            logger.info("📋 Using keyword-based template selection")

    def detect_tier(self, query: str, custom_template: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Detect the appropriate tier and template for a query.

        Args:
            query: User's question
            custom_template: Optional custom template provided by caller

        Returns:
            Dict with tier info and template guidance
        """
        return detect_tier(query, custom_template, self.use_semantic, self._semantic_selector)


def detect_tier(
    query: str,
    custom_template: Optional[Dict] = None,
    use_semantic: bool = True,  # ✅ Enabled by default for smarter matching
    semantic_selector=None
) -> Dict[str, Any]:
    """
    A2UI Orchestrator - 3-Tier Template Selection

    Args:
        query: User's question
        custom_template: Optional custom template provided by caller
        use_semantic: Enable semantic matching
        semantic_selector: SemanticTemplateSelector instance (optional)

    Returns:
        Dict with tier info and template guidance
    """
    logger.info("=" * 50)
    logger.info("🎯 A2UI TIER DETECTION STARTING")
    logger.info(f"📝 Query: '{query[:100]}{'...' if len(query) > 100 else ''}'")
    logger.info(f"🔧 Semantic mode: {use_semantic}")
    logger.info("=" * 50)
    
    query_lower = query.lower()

    # ==================== TIER 1a: CUSTOM TEMPLATE (API PARAMETER) ====================
    if custom_template:
        logger.info("🏆 TIER 1a MATCH: Custom template provided via API")
        logger.info(f"   Template type: {custom_template.get('type', 'custom')}")
        return {
            "tier": "tier1_custom",
            "tier_name": "Custom Template (API)",
            "template_type": custom_template.get("type", "custom"),
            "template": custom_template,
            "mode": "custom",
            "description": "Caller provided custom template via API parameter"
        }

    # ==================== TIER 1b: EXPLICIT TEMPLATE NAME (QUERY-BASED) ====================
    logger.debug("🔍 Checking TIER 1b: Explicit template keywords...")
    for template_type, keywords in TIER1_TEMPLATE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                logger.info(f"🏆 TIER 1b MATCH: Explicit template request detected!")
                logger.info(f"   Template: {template_type}")
                logger.info(f"   Matched keyword: '{keyword}'")
                return {
                    "tier": "tier1_explicit",
                    "tier_name": "Explicit Template Request",
                    "template_type": template_type,
                    "mode": "explicit_template",
                    "description": f"User requested {template_type} template",
                    "matched_keyword": keyword
                }
    logger.debug("   No explicit template keywords found")

    # ==================== TIER 2a: CRITICAL PATTERN OVERRIDES ====================
    # These patterns bypass semantic/keyword priority matching
    # Only catch queries where semantic model consistently fails or priority would be wrong
    logger.debug("🔍 Checking TIER 2a: Critical pattern overrides...")

    # Check for contact information queries (contact-card)
    contact_patterns = ["how to contact", "how can i contact", "contact information", "reach out", "get in touch"]
    contact_keywords = ["contact", "email", "phone", "address", "location", "office", "reach"]

    # Strong signal: query starts with contact pattern OR has multiple contact keywords
    starts_with_contact_pattern = any(query_lower.startswith(pattern) for pattern in contact_patterns)
    contact_keyword_count = sum(1 for kw in contact_keywords if kw in query_lower)

    if starts_with_contact_pattern or contact_keyword_count >= 2:
        logger.info(f"🎯 TIER 2a: Critical pattern override → contact-card")
        logger.info("   (Bypassing semantic/keyword for clear contact information request)")
        return {
            "tier": "tier2a_critical",
            "tier_name": "Critical Pattern Override",
            "template_type": "contact-card",
            "mode": "pattern_override",
            "description": "Query pattern indicates contact information request",
            "matched_pattern": "contact information",
            "selection_method": "critical_pattern"
        }

    # Check for "what is" / "who is" pattern (magazine-hero)
    # These single-subject overview queries should use magazine-hero
    if query_lower.startswith("what is") or query_lower.startswith("who is"):
        # Avoid false positives for specific content-type queries
        content_keywords = ["service", "team", "contact", "history", "difference", "project", "product"]
        has_specific_content = any(keyword in query_lower for keyword in content_keywords)

        if not has_specific_content:
            logger.info(f"🎯 TIER 2a: Critical pattern override → magazine-hero")
            logger.info("   (Bypassing semantic/keyword for single-subject overview query)")
            return {
                "tier": "tier2a_critical",
                "tier_name": "Critical Pattern Override",
                "template_type": "magazine-hero",
                "mode": "pattern_override",
                "description": "Question pattern indicates single-subject overview",
                "matched_pattern": "what is / who is",
                "selection_method": "critical_pattern"
            }

    logger.debug("   No critical pattern overrides matched")

    # ==================== TIER 2b: SEMANTIC MATCHING ====================
    # Use semantic understanding if available
    if use_semantic and semantic_selector:
        logger.debug("🔍 Checking TIER 2b: Semantic intent understanding...")
        try:
            # Use semantic selection directly (like reference service)
            template_type, confidence = semantic_selector.select_template(
                query=query,
                threshold=0.3  # Moderate threshold for quality template matching
            )

            if template_type and confidence >= 0.3:
                logger.info(f"🏆 TIER 2b MATCH (Semantic): Template selected!")
                logger.info(f"   Template: {template_type}")
                logger.info(f"   Confidence: {confidence:.3f}")
                return {
                    "tier": "tier2b_semantic",
                    "tier_name": "Semantic Template Selection",
                    "template_type": template_type,
                    "mode": "semantic",
                    "description": f"Semantic intent understanding (confidence: {confidence:.3f})",
                    "confidence": confidence,
                    "selection_method": "semantic"
                }
            else:
                logger.debug(f"   Semantic confidence too low ({confidence:.3f}), falling through...")
        except Exception as e:
            logger.warning(f"⚠️ Semantic selection failed: {e}")
            logger.warning("   Falling back to keyword matching")

    # ==================== TIER 2c: KEYWORD FALLBACK ====================
    # Fall back to keyword matching if semantic unavailable or low confidence
    logger.debug("🔍 Checking TIER 2c: Keyword pattern matching...")

    keyword_result = None
    keyword_match_info = None
    all_matches = []

    for pattern_name, pattern_config in TEMPLATE_PATTERNS.items():
        keywords = pattern_config["keywords"]
        priority = pattern_config.get("priority", 50)
        for keyword in keywords:
            if keyword in query_lower:
                all_matches.append({
                    "pattern": pattern_name,
                    "keyword": keyword,
                    "length": len(keyword),
                    "priority": priority,
                    "template": pattern_config["template_type"],
                    "description": pattern_config["description"]
                })
                logger.debug(f"   Found keyword match: '{keyword}' → {pattern_config['template_type']} (priority: {priority})")

    # Sort by: 1) priority (higher first), 2) keyword length (longer = more specific)
    if all_matches:
        all_matches.sort(key=lambda x: (x["priority"], x["length"]), reverse=True)
        best_match = all_matches[0]
        keyword_result = best_match["template"]
        keyword_match_info = best_match

        logger.info(f"🏆 TIER 2c MATCH (Keyword): Pattern detected!")
        logger.info(f"   Pattern: {keyword_match_info['pattern']}")
        logger.info(f"   Template: {keyword_match_info['template']}")
        logger.info(f"   Matched keyword: '{keyword_match_info['keyword']}'")
        logger.info(f"   Total matches found: {len(all_matches)}")
        return {
            "tier": "tier2c_keyword",
            "tier_name": "Keyword Pattern Match",
            "pattern": keyword_match_info["pattern"],
            "template_type": keyword_match_info["template"],
            "mode": "keyword",
            "description": keyword_match_info["description"],
            "matched_keyword": keyword_match_info["keyword"],
            "selection_method": "keyword"
        }

    # ==================== TIER 3: FALLBACK TO MAGAZINE HERO ====================
    logger.info("📋 TIER 3: No pattern match - using magazine hero fallback")
    logger.info("   This is normal for general questions without specific visual needs")
    return {
        "tier": "tier3_fallback",
        "tier_name": "Magazine Hero Fallback",
        "template_type": "magazine-hero",
        "mode": "fallback",
        "description": "No specific template matched, using magazine hero"
    }


def get_tier_metadata(tier_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate metadata about tier decision for response.

    Args:
        tier_info: Tier detection result

    Returns:
        Metadata dict for frontend
    """
    return {
        "tier": tier_info["tier"],
        "tier_name": tier_info["tier_name"],
        "template_type": tier_info["template_type"],
        "mode": tier_info["mode"],
        "description": tier_info["description"]
    }


# Test function
if __name__ == "__main__":
    test_queries = [
        # Tier 2a: Critical Pattern Overrides
        ("What is this assistant?", "magazine-hero"),  # "what is" → magazine-hero
        ("Tell me about your company?", "magazine-hero"),  # "what is" → magazine-hero
        ("Who is the CEO?", "magazine-hero"),  # "who is" → magazine-hero
        ("How can I contact you?", "contact-card"),  # contact pattern → contact-card
        ("What is your email and phone?", "contact-card"),  # multiple contact keywords → contact-card

        # Tier 2a exceptions (specific content keywords should NOT trigger override)
        ("What is your service?", "service-hover-reveal"),  # "service" → NOT magazine-hero
        ("What is your team?", "team-flip-cards"),  # "team" → NOT magazine-hero

        # Tier 2b/2c: Semantic/Keyword matching
        ("What are your products?", "template-grid"),
        ("Tell me about the company history", "timeline"),
        ("Show me a comparison chart of plans", "comparison-chart"),
        ("Who are the team members?", "team-flip-cards"),
        ("What services do you offer?", "service-hover-reveal"),
        ("Show me your projects", "template-grid"),
    ]

    print("\n" + "=" * 60)
    print("A2UI ORCHESTRATOR - TIER DETECTION EXAMPLES")
    print("=" * 60)

    correct = 0
    for query, expected in test_queries:
        tier_info = detect_tier(query, use_semantic=False)  # Test without semantic for consistency
        template = tier_info['template_type']
        is_correct = template == expected
        if is_correct:
            correct += 1

        status = "✅" if is_correct else "❌"
        print(f"\n{status} Query: \"{query}\"")
        print(f"   Expected: {expected}, Got: {template}")
        print(f"   Tier: {tier_info['tier_name']}")

    accuracy = (correct / len(test_queries)) * 100
    print("\n" + "=" * 60)
    print(f"ACCURACY: {correct}/{len(test_queries)} ({accuracy:.1f}%)")
    print("=" * 60)
