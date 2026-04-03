"""
LLM-based keyword extraction for Knowledge Graph highlighting.

This module extracts entity names/keywords from user queries using Google Gemini,
then intersects them with available graph nodes from LightRAG.

Model: Gemini 2.0 Flash via Google AI API
Latency: 100-300ms
"""

import asyncio
import os
import re
from typing import Dict, List, Optional, Set
from loguru import logger
import httpx

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Graph keyword extraction will fail.")


class GraphKeywordExtractor:
    """Extracts keywords from queries and matches them to graph nodes."""

    def __init__(
        self,
        api_key: str,
        lightrag_url: str = "",
        lightrag_api_key: str = None,
        model: str = "gemini-2.0-flash",
    ):
        """Initialize the keyword extractor.

        Args:
            api_key: Google AI API key
            lightrag_url: LightRAG API base URL
            lightrag_api_key: LightRAG API key for authentication
            model: Model name (default: gemini-2.0-flash)
        """
        self.api_key = api_key
        self.lightrag_url = lightrag_url.rstrip("/")
        self.lightrag_api_key = lightrag_api_key or os.getenv("LIGHTRAG_API_KEY", "")
        self.model = model
        self.client = None

        # Cache for graph nodes
        self._cached_node_ids: Set[str] = set()
        self._cached_node_labels: Dict[str, str] = {}  # lowercase label -> node_id
        self._cached_node_names: Dict[str, str] = {}   # node_id -> display name
        self._cached_name_to_id: Dict[str, str] = {}   # lowercase name -> node_id

        if not GOOGLE_AI_AVAILABLE:
            logger.error("Google AI SDK not available. Keyword extraction will fail.")
            return

        # Configure Google AI
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

        logger.info(f"GraphKeywordExtractor initialized (model: {model}, lightrag: {lightrag_url})")

    async def fetch_graph_nodes(self, force_refresh: bool = False) -> Set[str]:
        """Fetch available graph node IDs from LightRAG.

        Args:
            force_refresh: Force cache refresh

        Returns:
            Set of node IDs (lowercase for matching)
        """
        if self._cached_node_ids and not force_refresh:
            return self._cached_node_ids

        try:
            url = f"{self.lightrag_url}/graphs?label=*&max_depth=10"
            headers = {}
            if self.lightrag_api_key:
                headers["X-API-Key"] = self.lightrag_api_key
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

            # Extract node IDs, labels, and names
            self._cached_node_ids = set()
            self._cached_node_labels = {}
            self._cached_node_names = {}
            self._cached_name_to_id = {}

            for node in data.get("nodes", []):
                node_id = node.get("id", "")
                if not node_id:
                    continue

                # Get display name: prefer labels, then properties.name, then id
                labels = node.get("labels", [])
                props = node.get("properties", {})
                display_name = labels[0] if labels else (props.get("name") or props.get("entity_name") or node_id)

                # Store mappings
                self._cached_node_ids.add(node_id)
                self._cached_node_names[node_id] = display_name
                self._cached_name_to_id[display_name.lower()] = node_id

                # Also map by all labels
                for label in labels:
                    if label:
                        self._cached_name_to_id[label.lower()] = node_id

            logger.info(f"[GraphKeywords] Cached {len(self._cached_node_ids)} nodes with names")
            # Log a sample of names for debugging
            sample_names = list(self._cached_node_names.values())[:10]
            logger.debug(f"[GraphKeywords] Sample node names: {sample_names}")
            return self._cached_node_ids

        except Exception as e:
            logger.error(f"[GraphKeywords] Failed to fetch graph nodes: {e}")
            return self._cached_node_ids  # Return cached if fetch fails

    async def select_nodes_from_graph(self, query: str, answer: str = "") -> List[str]:
        """Use LLM to select relevant nodes from the actual graph node list.

        Args:
            query: User query text
            answer: Bot's answer text (for better context)

        Returns:
            List of node IDs that should be highlighted
        """
        if not query or not query.strip():
            return []

        if not self.client:
            logger.warning("[GraphKeywords] LLM client not available")
            return []

        # Get unique node display names from cache
        unique_names = list(set(self._cached_node_names.values()))
        if not unique_names:
            logger.warning("[GraphKeywords] No graph nodes cached")
            return []

        # Limit nodes for prompt (keep it reasonable)
        names_for_prompt = unique_names[:150]
        nodes_list = ", ".join(names_for_prompt)
        logger.debug(f"[GraphKeywords] Sending {len(names_for_prompt)} node names to LLM")

        try:
            # Build context section
            context = f"USER QUERY: {query}"
            if answer:
                context += f"\nBOT ANSWER: {answer}"

            prompt = """You are selecting nodes to highlight in a knowledge graph visualization.

AVAILABLE GRAPH NODES (select ONLY from this list):
{nodes}

{context}

TASK: Select 4-5 MOST RELEVANT nodes from the AVAILABLE list, ordered by relevance.

Rules:
1. ONLY return nodes that EXACTLY match names in the available list
2. Select 4-5 nodes maximum
3. ORDER BY RELEVANCE: most important first, least important last
4. Prioritize: entities mentioned in answer > main topics > related concepts
5. Return ONLY a comma-separated list of exact node names, nothing else

Selected nodes (4-5, ordered by relevance):"""

            response = await asyncio.to_thread(
                self.client.generate_content,
                prompt.format(nodes=nodes_list, context=context),
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Very low for precise selection
                    max_output_tokens=300,
                )
            )

            raw_response = response.text.strip()
            logger.debug(f"[GraphKeywords] LLM response: {raw_response}")

            # Parse comma-separated node names
            selected_names = [n.strip() for n in raw_response.split(",") if n.strip()]

            # Convert names to node IDs
            validated_ids = []
            validated_names = []

            for name in selected_names:
                name_clean = re.sub(r'^["\']|["\']$', '', name).strip()
                name_lower = name_clean.lower()

                # Look up node ID by name
                if name_lower in self._cached_name_to_id:
                    node_id = self._cached_name_to_id[name_lower]
                    validated_ids.append(node_id)
                    validated_names.append(name_clean)
                # Also check if it's already a valid node ID
                elif name_clean in self._cached_node_ids:
                    validated_ids.append(name_clean)
                    validated_names.append(self._cached_node_names.get(name_clean, name_clean))

            # Deduplicate while preserving order
            seen = set()
            unique_ids = []
            unique_names = []
            for i, node_id in enumerate(validated_ids):
                if node_id not in seen:
                    seen.add(node_id)
                    unique_ids.append(node_id)
                    unique_names.append(validated_names[i])

            logger.info(f"[GraphKeywords] Selected nodes: {unique_names[:5]}")
            return unique_ids[:5]  # Return node IDs, limit to 5

        except Exception as e:
            logger.error(f"[GraphKeywords] Node selection failed: {e}")
            return []

    async def extract_topic_and_type(
        self, query: str, answer: str = "", previous_topics: List[str] = None
    ) -> Dict[str, str]:
        """Extract conversation topic and determine its relationship to previous topics.

        Args:
            query: User query text
            answer: Bot's answer text
            previous_topics: List of previous conversation topics

        Returns:
            Dict with topic, topicType, and optionally parentTopic
        """
        if not query or not query.strip():
            return {"topic": "", "topicType": "new", "parentTopic": None}

        if not self.client:
            # Fallback: extract topic from query
            topic = self._extract_topic_fallback(query)
            return {"topic": topic, "topicType": "new", "parentTopic": None}

        previous_topics = previous_topics or []

        try:
            # Build previous topics context
            prev_context = ""
            if previous_topics:
                prev_context = f"\nPREVIOUS TOPICS (in order): {', '.join(previous_topics[-5:])}"

            prompt = """Analyze this conversation turn and extract the topic.

USER QUERY: {query}
BOT ANSWER: {answer}{prev_context}

TASK: Extract the conversation topic and determine its relationship to previous topics.

1. TOPIC: A concise topic (2-5 words) describing what this turn is about
2. TYPE: One of:
   - "new" = Completely new topic, unrelated to previous
   - "continuation" = Same topic as the last one, continuing discussion
   - "branch" = Related to a previous topic but exploring a different aspect
3. PARENT: If TYPE is "branch", which previous topic does it branch from?

Return in this exact format (one line each):
TOPIC: <topic>
TYPE: <new|continuation|branch>
PARENT: <parent topic or none>"""

            response = await asyncio.to_thread(
                self.client.generate_content,
                prompt.format(
                    query=query,
                    answer=answer[:200] if answer else "N/A",
                    prev_context=prev_context
                ),
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=150,
                )
            )

            raw_response = response.text.strip()
            logger.debug(f"[GraphKeywords] Topic extraction response: {raw_response}")

            # Parse response
            topic = ""
            topic_type = "new"
            parent_topic = None

            for line in raw_response.split("\n"):
                line = line.strip()
                if line.upper().startswith("TOPIC:"):
                    topic = line[6:].strip()
                elif line.upper().startswith("TYPE:"):
                    t = line[5:].strip().lower()
                    if t in ("new", "continuation", "branch"):
                        topic_type = t
                elif line.upper().startswith("PARENT:"):
                    p = line[7:].strip()
                    if p.lower() != "none" and p:
                        parent_topic = p

            # Validate topic
            if not topic:
                topic = self._extract_topic_fallback(query)

            logger.info(f"[GraphKeywords] Topic: '{topic}', Type: {topic_type}, Parent: {parent_topic}")

            return {
                "topic": topic,
                "topicType": topic_type,
                "parentTopic": parent_topic
            }

        except Exception as e:
            logger.error(f"[GraphKeywords] Topic extraction failed: {e}")
            return {
                "topic": self._extract_topic_fallback(query),
                "topicType": "new",
                "parentTopic": None
            }

    def _extract_topic_fallback(self, query: str) -> str:
        """Simple fallback topic extraction without LLM."""
        if not query:
            return ""

        # Remove question words and clean up
        topic = query.strip()
        for prefix in ["what", "who", "where", "when", "why", "how", "can", "could",
                       "would", "should", "is", "are", "do", "does", "tell me about",
                       "explain", "describe"]:
            if topic.lower().startswith(prefix + " "):
                topic = topic[len(prefix) + 1:]
                break

        # Remove trailing punctuation
        topic = topic.rstrip("?!.,")

        # Capitalize and limit length
        topic = topic.strip()
        if topic:
            topic = topic[0].upper() + topic[1:]
        if len(topic) > 35:
            topic = topic[:32] + "..."

        return topic

    async def extract_keywords_llm(self, query: str) -> List[str]:
        """Legacy method - now uses select_nodes_from_graph."""
        return await self.select_nodes_from_graph(query)

    def _fallback_extract(self, query: str) -> List[str]:
        """Simple fallback keyword extraction without LLM."""
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "under", "again", "further", "then", "once", "here",
            "there", "when", "where", "why", "how", "all", "each", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own",
            "same", "so", "than", "too", "very", "just", "and", "but", "if", "or",
            "because", "until", "while", "about", "against", "what", "which", "who",
            "this", "that", "these", "those", "am", "i", "me", "my", "you", "your",
            "he", "him", "his", "she", "her", "it", "its", "we", "us", "our", "they",
            "them", "their", "tell", "know", "get", "give", "go", "come", "make",
            "take", "see", "look", "want", "use", "find", "also", "way", "many"
        }

        # Extract words, keeping multi-word entities together if capitalized
        words = query.replace("?", "").replace("!", "").replace(".", "").split()
        keywords = []

        for word in words:
            cleaned = word.strip().lower()
            if cleaned and len(cleaned) > 2 and cleaned not in stop_words:
                keywords.append(word.strip())  # Keep original case

        return list(dict.fromkeys(keywords))[:5]  # Dedupe and limit

    def _normalize_for_matching(self, text: str) -> str:
        """Normalize text for fuzzy matching by removing spaces and special chars."""
        return re.sub(r'[\s\-_]+', '', text.lower())

    def _similarity_ratio(self, s1: str, s2: str) -> float:
        """Calculate similarity ratio between two strings (0.0 to 1.0)."""
        if not s1 or not s2:
            return 0.0
        if s1 == s2:
            return 1.0

        # Use simple character-based similarity
        # Count matching characters in order
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0

        # Longest common subsequence ratio
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])

        lcs_length = dp[len1][len2]
        return (2.0 * lcs_length) / (len1 + len2)

    async def get_matching_keywords(
        self, query: str, answer: str = "", previous_topics: List[str] = None
    ) -> Dict:
        """Select relevant graph nodes and extract topic based on query and answer.

        Args:
            query: User query text
            answer: Bot's answer text (optional, improves selection)
            previous_topics: List of previous conversation topics for context

        Returns:
            Dict with:
                - query: Original query
                - answer: Bot answer (if provided)
                - matched: List of node IDs to highlight
                - graph_node_count: Total nodes in graph
                - topic: Extracted conversation topic
                - topicType: "new", "continuation", or "branch"
                - parentTopic: Parent topic if branching
        """
        # Extract topic using LLM (doesn't need LightRAG)
        topic_info = await self.extract_topic_and_type(query, answer, previous_topics)

        # Try to fetch graph nodes and select matching ones (optional - needs LightRAG)
        matched = []
        try:
            await self.fetch_graph_nodes()
            if self._cached_node_ids:
                matched = await self.select_nodes_from_graph(query, answer)
        except Exception as e:
            logger.warning(f"[GraphKeywords] Graph node selection skipped: {e}")

        logger.info(
            f"[GraphKeywords] Query: '{query[:40]}...' → "
            f"Topic: '{topic_info.get('topic')}', Matched nodes: {len(matched)}"
        )

        return {
            "query": query,
            "answer": answer[:100] if answer else "",
            "matched": matched,
            "graph_node_count": len(self._cached_node_ids),
            "topic": topic_info.get("topic", ""),
            "topicType": topic_info.get("topicType", "new"),
            "parentTopic": topic_info.get("parentTopic"),
        }

    def get_status(self) -> Dict:
        """Get extractor status."""
        return {
            "model": self.model,
            "provider": "google_ai",
            "available": GOOGLE_AI_AVAILABLE and self.client is not None,
            "lightrag_url": self.lightrag_url,
            "cached_nodes": len(self._cached_node_ids),
        }


# Global instance
_extractor: Optional[GraphKeywordExtractor] = None


def get_graph_keyword_extractor(
    api_key: str = None,
    lightrag_url: str = None,
) -> GraphKeywordExtractor:
    """Get or create global GraphKeywordExtractor instance.

    Args:
        api_key: Google AI API key (required on first call, or from env)
        lightrag_url: LightRAG API URL (optional, defaults to env or localhost)
    """
    global _extractor

    if _extractor is None:
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
        if api_key is None:
            raise ValueError("Google API key required to initialize keyword extractor")

        if lightrag_url is None:
            lightrag_url = os.getenv("LIGHTRAG_URL", os.getenv("LIGHTRAG_BASE_URL", ""))

        lightrag_api_key = os.getenv("LIGHTRAG_API_KEY", "")
        _extractor = GraphKeywordExtractor(api_key=api_key, lightrag_url=lightrag_url, lightrag_api_key=lightrag_api_key)

    return _extractor
