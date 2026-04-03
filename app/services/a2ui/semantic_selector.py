"""
Semantic Template Selector - Intent Understanding using Sentence Transformers

This module uses sentence embeddings and cosine similarity to understand user intent
and select the most appropriate A2UI template, moving beyond simple keyword matching.

Features:
- Semantic similarity matching using pre-trained embeddings
- Intent understanding (not just keyword matching)
- Fast inference (~50-100ms per query)
- No additional LLM calls required
- Handles typos, variations, and natural language
- Dynamically learns from template metadata (no hardcoding)

Model: multi-qa-MiniLM-L6-cos-v1
- Trained on 215M Q&A pairs
- Optimized for question-answering tasks
- Size: ~80MB
- Inference: ~50ms per query
"""

from typing import Dict, Tuple, Optional
from loguru import logger

# Lazy import to avoid startup delay if not used
SentenceTransformer = None
util = None


def _load_sentence_transformers():
    """Lazy load sentence-transformers to avoid import overhead."""
    global SentenceTransformer, util
    if SentenceTransformer is None:
        from sentence_transformers import SentenceTransformer as ST, util as st_util
        SentenceTransformer = ST
        util = st_util


class SemanticTemplateSelector:
    """
    Semantic template selector using sentence embeddings.

    Uses the multi-qa-MiniLM-L6-cos-v1 model optimized for question-answering.
    Trained on 215M Q&A pairs for superior query understanding.

    Attributes:
        model: SentenceTransformer model instance
        template_embeddings: Pre-computed embeddings for each template
    """

    def __init__(self, model_name: str = "multi-qa-MiniLM-L6-cos-v1"):
        """
        Initialize the semantic selector.

        Dynamically builds template embeddings from template_library metadata.
        No hardcoding - learns from existing template definitions.

        Args:
            model_name: Sentence transformer model to use
                       Default: "multi-qa-MiniLM-L6-cos-v1" (QA-optimized)
        """
        _load_sentence_transformers()

        logger.info("=" * 60)
        logger.info("🧠 SEMANTIC TEMPLATE SELECTOR INITIALIZING")
        logger.info(f"   Model: {model_name}")
        logger.info("=" * 60)

        logger.info(f"📥 Loading Sentence Transformer model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        logger.info("✅ Model loaded successfully")

        # Pre-compute template embeddings from metadata
        self._build_template_embeddings()

        logger.info("=" * 60)
        logger.info("🧠 SEMANTIC SELECTOR READY")
        logger.info(f"   Templates indexed: {len(self.template_embeddings)}")
        logger.info("=" * 60)

    def _build_template_embeddings(self):
        """
        Build embeddings from template library metadata.

        Combines multiple semantic signals:
        - Template name
        - Description
        - Use cases
        - Trigger keywords
        """
        from .template_library import list_available_templates

        logger.info("📊 Building template embeddings from template_library metadata...")
        template_metadata = list_available_templates()

        self.template_embeddings = {}
        self.template_descriptions = {}  # Store for debugging

        for template in template_metadata["templates"]:
            template_type = template["type"]

            # Build semantic description from template metadata
            # Combine: name + description + use_cases + trigger_keywords
            semantic_parts = [
                template["name"],
                template["description"]
            ]

            # Add use cases (what the template is used for)
            if template.get("use_cases"):
                semantic_parts.extend(template["use_cases"])

            # Add trigger keywords (natural language context)
            if template.get("trigger_keywords"):
                semantic_parts.extend(template["trigger_keywords"])

            # Combine into single semantic representation
            combined_description = " | ".join(semantic_parts)
            self.template_descriptions[template_type] = combined_description

            # Encode to embedding
            embedding = self.model.encode(combined_description, convert_to_tensor=True)
            self.template_embeddings[template_type] = embedding

            # Debug logging with breakdown
            use_cases_count = len(template.get("use_cases", []))
            keywords_count = len(template.get("trigger_keywords", []))
            logger.debug(
                f"   ✅ {template_type}: {len(semantic_parts)} signals "
                f"(desc: 2, use_cases: {use_cases_count}, keywords: {keywords_count})"
            )

        logger.info(f"✅ Pre-computed embeddings for {len(self.template_embeddings)} templates")

    def select_template(
        self,
        query: str,
        threshold: float = 0.3
    ) -> Tuple[Optional[str], float]:
        """
        Select the best matching template based on semantic similarity.

        Args:
            query: User's question
            threshold: Minimum similarity score (0-1) to consider a match
                      Default: 0.3 (moderate threshold for quality template matching)

        Returns:
            Tuple of (template_type, confidence_score)
            Returns (None, 0.0) if no template exceeds threshold

        Examples:
            >>> selector = SemanticTemplateSelector()
            >>> template, score = selector.select_template("How do I reach you?")
            >>> template
            'contact-card'
            >>> score > 0.3
            True
        """
        # Encode the user query
        query_embedding = self.model.encode(query, convert_to_tensor=True)

        # Compute similarity with each template
        best_template = None
        best_score = -1.0
        scores = {}

        for template_type, template_embedding in self.template_embeddings.items():
            similarity = util.cos_sim(query_embedding, template_embedding)
            score = float(similarity[0][0])  # Extract scalar value
            scores[template_type] = score

            if score > best_score:
                best_score = score
                best_template = template_type

        # Log similarity scores for debugging
        logger.debug(f"🎯 Semantic similarity scores for query: '{query[:60]}...'")
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for template, score in sorted_scores[:5]:  # Top 5
            indicator = "✅" if template == best_template else "  "
            logger.debug(f"   {indicator} {template}: {score:.3f}")

        # Return None if best score doesn't meet threshold
        if best_score < threshold:
            logger.debug(f"⚠️ Best score ({best_score:.3f}) below threshold ({threshold})")
            return None, best_score

        logger.info(f"✅ Semantic match: {best_template} (confidence: {best_score:.3f})")
        return best_template, best_score

    def select_template_with_fallback(
        self,
        query: str,
        keyword_result: Optional[str] = None,
        semantic_threshold: float = 0.3,
        confidence_threshold: float = 0.5
    ) -> Tuple[str, float, str]:
        """
        Hybrid approach: Use semantic matching with keyword fallback.

        Strategy:
        1. Try semantic matching
        2. If confidence is high (>0.5), use semantic result
        3. If confidence is medium (0.3-0.5) and keyword result exists, use keyword
        4. If confidence is low (<0.3), use keyword result or default to magazine-hero

        Args:
            query: User's question
            keyword_result: Result from keyword matching (optional)
            semantic_threshold: Minimum score to consider semantic match
            confidence_threshold: Score above which we trust semantic over keywords

        Returns:
            Tuple of (template_type, confidence_score, selection_method)
            selection_method: "semantic", "keyword_fallback", or "default"
        """
        semantic_template, semantic_score = self.select_template(query, semantic_threshold)

        # High confidence semantic match
        if semantic_score >= confidence_threshold:
            logger.info(f"✅ High confidence semantic match ({semantic_score:.3f})")
            return semantic_template, semantic_score, "semantic"

        # Medium confidence - prefer keyword if available
        if semantic_template and semantic_threshold <= semantic_score < confidence_threshold:
            if keyword_result:
                logger.info(f"⚠️ Medium confidence ({semantic_score:.3f}), using keyword fallback: {keyword_result}")
                return keyword_result, semantic_score, "keyword_fallback"
            else:
                logger.info(f"⚠️ Medium confidence ({semantic_score:.3f}), no keyword match, using semantic")
                return semantic_template, semantic_score, "semantic"

        # Low confidence or no match - use keyword or default
        if keyword_result:
            logger.info(f"⚠️ Low semantic confidence, using keyword fallback: {keyword_result}")
            return keyword_result, 0.0, "keyword_fallback"

        logger.info(f"⚠️ No matches found, defaulting to magazine-hero")
        return "magazine-hero", 0.0, "default"

    def get_all_scores(self, query: str) -> Dict[str, float]:
        """
        Get similarity scores for all templates.

        Useful for debugging and understanding template selection.

        Args:
            query: User's question

        Returns:
            Dict mapping template_type to similarity score
        """
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        scores = {}

        for template_type, template_embedding in self.template_embeddings.items():
            similarity = util.cos_sim(query_embedding, template_embedding)
            scores[template_type] = float(similarity[0][0])

        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


# Global instance (lazy loaded)
_semantic_selector: Optional[SemanticTemplateSelector] = None
_initialization_error: Optional[str] = None


def get_semantic_selector() -> Optional[SemanticTemplateSelector]:
    """
    Get or create the global semantic selector instance.

    Uses lazy loading to avoid loading the model on import.
    Model is loaded on first use (~4 seconds).

    Returns:
        SemanticTemplateSelector instance or None if initialization failed
    """
    global _semantic_selector, _initialization_error

    if _initialization_error:
        logger.debug(f"Semantic selector unavailable: {_initialization_error}")
        return None

    if _semantic_selector is None:
        try:
            _semantic_selector = SemanticTemplateSelector()
        except ImportError as e:
            _initialization_error = f"sentence-transformers not installed: {e}"
            logger.warning(f"⚠️ {_initialization_error}")
            return None
        except Exception as e:
            _initialization_error = f"Failed to initialize: {e}"
            logger.error(f"❌ Semantic selector initialization failed: {e}")
            return None

    return _semantic_selector


def is_semantic_available() -> bool:
    """Check if semantic selector can be initialized."""
    try:
        _load_sentence_transformers()
        return True
    except ImportError:
        return False


# ==================== EXAMPLES AND TESTING ====================

if __name__ == "__main__":
    print("=" * 80)
    print("SEMANTIC TEMPLATE SELECTOR - TEST EXAMPLES")
    print("=" * 80)

    # Initialize selector
    selector = SemanticTemplateSelector()

    # Test queries that should work with semantic understanding
    test_queries = [
        # Contact intent (various phrasings)
        ("How do I reach you?", "contact-card"),
        ("What's your email address?", "contact-card"),
        ("Where are you located?", "contact-card"),
        ("I need to get in touch", "contact-card"),

        # Timeline intent
        ("When was this company started?", "timeline"),
        ("Tell me about your history", "timeline"),
        ("What are your milestones?", "timeline"),

        # Team intent
        ("Who's on the team?", "team-flip-cards"),
        ("Tell me about your people", "team-flip-cards"),
        ("Who are the founders?", "team-flip-cards"),

        # Services intent
        ("What do you do?", "service-hover-reveal"),
        ("What services do you offer?", "service-hover-reveal"),
        ("How can you help me?", "service-hover-reveal"),

        # Comparison intent
        ("What's the difference between X and Y?", "comparison-chart"),
        ("Which one is better?", "comparison-chart"),
        ("Compare these options", "comparison-chart"),

        # Statistics intent
        ("How many users do you have?", "stats-flow-layout"),
        ("What are your metrics?", "stats-flow-layout"),
        ("Show me the numbers", "stats-flow-layout"),

        # FAQ intent
        ("Do you have any common questions?", "faq-accordion"),
        ("What do people usually ask?", "faq-accordion"),

        # Projects/Products intent
        ("Show me your products", "template-grid"),
        ("What projects have you done?", "template-grid"),
    ]

    print(f"\n🧪 Testing {len(test_queries)} queries...\n")

    correct = 0
    for query, expected in test_queries:
        template, score = selector.select_template(query)
        is_correct = template == expected
        if is_correct:
            correct += 1

        status = "✅" if is_correct else "❌"
        print(f"{status} Query: '{query}'")
        print(f"   Expected: {expected}, Got: {template} (score: {score:.3f})\n")

    accuracy = (correct / len(test_queries)) * 100
    print("=" * 80)
    print(f"ACCURACY: {correct}/{len(test_queries)} ({accuracy:.1f}%)")
    print("=" * 80)
