"""
RAG (Retrieval Augmented Generation) service for the Voice Assistant.

This module provides RAG functionality using different backends:
- LightRAG: External LightRAG API integration with A2UI template support
- Pinecone: Vector database with LangChain integration
- Mock: For testing purposes

A2UI Integration:
- LightRAG can accept A2UI templates and fill them with retrieved data
- Templates are sent with the query, and LLM fills them from RAG context
- This enables dynamic visual responses based on knowledge base content
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

# Shared HTTP client for connection pooling and reuse
_shared_client: Optional[httpx.AsyncClient] = None


def get_shared_client(timeout: float = 30.0, verify: bool = False) -> httpx.AsyncClient:
    """Get or create a shared HTTP client with connection pooling.
    
    Args:
        timeout: Request timeout in seconds
        verify: Whether to verify SSL certificates
        
    Returns:
        Shared httpx.AsyncClient instance
    """
    global _shared_client
    
    if _shared_client is None or _shared_client.is_closed:
        # Check if HTTP/2 is available (requires h2 package)
        try:
            import h2
            use_http2 = True
        except ImportError:
            use_http2 = False
            logger.warning("h2 package not installed, HTTP/2 disabled. Install with: pip install httpx[http2]")
        
        _shared_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=5.0, read=timeout),
            verify=verify,
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5,
                keepalive_expiry=60.0,  # Increased to 60 seconds for better connection reuse
            ),
            http2=use_http2,  # Use HTTP/2 if available, otherwise HTTP/1.1
        )
        logger.debug(f"Created shared HTTP client with connection pooling (HTTP/2: {use_http2})")
    
    return _shared_client


@dataclass
class A2UIResponse:
    """Response from RAG service with A2UI support.

    Attributes:
        text: Natural language response text
        a2ui: A2UI document structure (filled template) or None
        references: List of source document references
        tier: Template tier that was used
        template_type: Type of template that was filled
        query_time_ms: Total query time in milliseconds
    """
    text: str
    a2ui: Optional[Dict[str, Any]] = None
    references: Optional[List[Dict[str, Any]]] = None
    tier: Optional[str] = None
    template_type: Optional[str] = None
    query_time_ms: float = 0.0


class BaseRAGService(ABC):
    """Abstract base class for RAG services."""

    @abstractmethod
    async def get_response(self, query: str) -> str:
        """Query the RAG service and get a response.

        Args:
            query: The user's question

        Returns:
            The RAG response string
        """
        pass

    async def get_response_with_a2ui(
        self,
        query: str,
        a2ui_template: Optional[Dict[str, Any]] = None,
        template_instructions: Optional[str] = None,
    ) -> A2UIResponse:
        """Query the RAG service with A2UI template support.

        This method allows sending an A2UI template to be filled by the RAG/LLM.
        Default implementation falls back to get_response() without A2UI.

        Args:
            query: The user's question
            a2ui_template: Optional A2UI template structure to fill
            template_instructions: Optional instructions for template filling

        Returns:
            A2UIResponse with text and optionally filled A2UI template
        """
        # Default implementation: just get text response
        text = await self.get_response(query)
        return A2UIResponse(text=text)

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get the service status.

        Returns:
            Status dictionary
        """
        pass

    @abstractmethod
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update the service configuration.

        Args:
            config: New configuration parameters
        """
        pass


class RAGService(BaseRAGService):
    """Mock RAG service for testing and development."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the mock RAG service.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        logger.info("Initialized Mock RAG Service")

    async def get_response(self, query: str) -> str:
        """Return a mock response.

        Args:
            query: The user's question

        Returns:
            Mock response string
        """
        logger.info(f"Mock RAG query: {query}")
        return f"This is a mock response for: {query}"

    def get_status(self) -> Dict[str, Any]:
        """Get mock service status."""
        return {"type": "mock", "status": "active"}

    def update_config(self, config: Dict[str, Any]) -> None:
        """Update configuration."""
        self.config.update(config)


class LightRAGService(BaseRAGService):
    """Service for interacting with LightRAG API.

    Attributes:
        api_url: Base URL of the LightRAG API
        mode: Query mode (mix, local, global, hybrid)
        top_k: Number of results to retrieve
        timeout: API timeout in seconds
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the LightRAG service.

        Args:
            config: Configuration dictionary containing:
                - api_url: Base URL of the LightRAG API
                - mode: Query mode (mix, local, global, hybrid, naive)
                    - "local": Fastest, entity-focused (recommended for speed)
                    - "naive": Vector search only (fastest but less accurate)
                    - "global": Slower, pattern analysis
                    - "mix": Balanced but slower
                - top_k: Number of results to retrieve (lower = faster)
                - timeout: API timeout in seconds
                - use_connection_pooling: Use shared HTTP client (default: True)
        """
        self.config = config or {}
        api_url_raw = self.config.get("api_url", "http://localhost:9621")
        # Remove trailing slash to avoid double slashes when appending paths
        self.api_url = api_url_raw.rstrip("/")
        self.api_key = self.config.get("api_key", "")
        # Use "local" mode for faster responses (entity-focused retrieval)
        self.mode = self.config.get("mode", "local")
        # Lower top_k for faster retrieval (3 is optimal balance)
        self.top_k = self.config.get("top_k", 3)
        self.chunk_top_k = self.config.get("chunk_top_k", 10)
        self.max_entity_tokens = self.config.get("max_entity_tokens", 600)
        self.max_relation_tokens = self.config.get("max_relation_tokens", 600)
        self.max_total_tokens = self.config.get("max_total_tokens", 1000)
        # Reduced timeout for faster failure detection
        self.timeout = self.config.get("timeout", 20)
        self.use_connection_pooling = self.config.get("use_connection_pooling", True)

        logger.info(
            f"Initialized LightRAG Service: {self.api_url}, "
            f"mode={self.mode}, top_k={self.top_k}, chunk_top_k={self.chunk_top_k}, "
            f"max_entity_tokens={self.max_entity_tokens}, max_relation_tokens={self.max_relation_tokens}, "
            f"max_total_tokens={self.max_total_tokens}, timeout={self.timeout}s"
        )

    async def get_response(self, query: str) -> str:
        """Query the LightRAG API and get a response using streaming for faster first-token.

        Optimizations applied:
        - Connection pooling for reduced latency
        - Streaming for faster first-token response
        - Optimized payload (top_k, mode)
        - Early error detection

        Args:
            query: The user's question

        Returns:
            The RAG response string
        """
        start_time = time.time()
        try:
            logger.debug(f"RAG query start: '{query[:80]}'")
            logger.debug(f"LightRAG query: {query}")

            # Optimized payload: include all RAG parameters
            payload = {
                "query": query,
                "mode": self.mode,
                "stream": True,
                "top_k": self.top_k,  # Number of top results to retrieve
                "chunk_top_k": self.chunk_top_k,  # Number of top chunks to retrieve
                "max_entity_tokens": self.max_entity_tokens,  # Maximum tokens for entity extraction
                "max_relation_tokens": self.max_relation_tokens,  # Maximum tokens for relation extraction
                "max_total_tokens": self.max_total_tokens,  # Maximum total tokens for response
            }

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/x-ndjson",
                "ngrok-skip-browser-warning": "true",
                "Connection": "keep-alive",  # Reuse connections
            }
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            # Use shared client for connection pooling (faster subsequent requests)
            if self.use_connection_pooling:
                client = get_shared_client(timeout=self.timeout, verify=False)
            else:
                client = httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout, connect=5.0),
                    verify=False,
                    limits=httpx.Limits(max_connections=1),
                )

            # Use streaming endpoint for faster first-token response
            full_response = ""
            first_chunk_time = None
            try:
                async with client.stream(
                    "POST",
                    f"{self.api_url}/query/stream",
                    json=payload,
                    headers=headers,
                ) as response:
                    response.raise_for_status()

                    # Parse NDJSON streaming response
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                # Parse each JSON line (NDJSON format)
                                data = json.loads(line)

                                # Skip references line, get response chunks
                                if "response" in data:
                                    chunk = data.get("response", "")
                                    if chunk and first_chunk_time is None:
                                        first_chunk_time = time.time()
                                        logger.debug(f"RAG first chunk: {first_chunk_time - start_time:.3f}s")
                                    full_response += chunk
                                elif "error" in data:
                                    logger.error(f"LightRAG streaming error: {data.get('error')}")
                                    return "I encountered an error while searching the knowledge base."
                            except json.JSONDecodeError:
                                # Skip non-JSON lines (like empty lines)
                                continue
            finally:
                # Only close if we created a new client (not shared)
                if not self.use_connection_pooling:
                    await client.aclose()

            end_time = time.time()
            total_time = end_time - start_time
            logger.debug(f"RAG complete: {total_time:.3f}s, {len(full_response)} chars")

            if "[no-context]" in full_response:
                logger.warning("LightRAG: No context found for query")
                return "I don't have specific information about that in my knowledge base."

            logger.debug(f"LightRAG response length: {len(full_response)} chars")
            return full_response

        except httpx.TimeoutException:
            logger.error("LightRAG API timeout")
            return "I'm having trouble accessing the knowledge base. Please try again."
        except httpx.HTTPStatusError as e:
            logger.error(f"LightRAG API error: {e.response.status_code}")
            return "I encountered an error while searching the knowledge base."
        except Exception as e:
            logger.error(f"LightRAG error: {e}")
            return f"I encountered an error: {str(e)}"

    async def get_response_with_a2ui(
        self,
        query: str,
        a2ui_template: Optional[Dict[str, Any]] = None,
        template_instructions: Optional[str] = None,
    ) -> A2UIResponse:
        """Query LightRAG with A2UI template support.

        This method sends the query along with an A2UI template to LightRAG.
        LightRAG's LLM will fill the template with data from the knowledge base.

        Args:
            query: The user's question
            a2ui_template: A2UI template structure to fill (from template library)
            template_instructions: Instructions for how to fill the template

        Returns:
            A2UIResponse with text response and filled A2UI template
        """
        start_time = time.time()

        template_type = a2ui_template.get("root", {}).get("type", "none") if a2ui_template else "none"
        logger.debug(f"RAG+A2UI query: '{query[:60]}' template={template_type}")

        try:
            # Build payload with A2UI template
            payload = {
                "query": query,
                "mode": self.mode,
                "stream": False,  # Non-streaming for A2UI (need complete response)
                "top_k": self.top_k,
                "chunk_top_k": self.chunk_top_k,
                "max_entity_tokens": self.max_entity_tokens,
                "max_relation_tokens": self.max_relation_tokens,
                "max_total_tokens": self.max_total_tokens,
                "include_references": True,
            }

            # Add A2UI template if provided
            if a2ui_template:
                payload["a2ui_template"] = a2ui_template
                payload["response_format"] = "both"  # Request both text and A2UI

                # Default instructions if not provided
                if not template_instructions:
                    template_instructions = (
                        "Fill this A2UI template with actual data from the retrieved context. "
                        "Add as many items as the data supports. Use REAL data from the context. "
                        "Do NOT return empty arrays or placeholder text."
                    )
                payload["template_instructions"] = template_instructions

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "ngrok-skip-browser-warning": "true",
                "Connection": "keep-alive",
            }
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            # Use shared client for connection pooling
            if self.use_connection_pooling:
                client = get_shared_client(timeout=self.timeout, verify=False)
            else:
                client = httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout, connect=5.0),
                    verify=False,
                    limits=httpx.Limits(max_connections=1),
                )

            try:
                # Use non-streaming endpoint for A2UI (need complete JSON response)
                response = await client.post(
                    f"{self.api_url}/query",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                response_data = response.json()

            finally:
                if not self.use_connection_pooling:
                    await client.aclose()

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"⏱️ RAG+A2UI query completed in {elapsed_ms:.1f}ms")

            # Parse response
            text_response = response_data.get("response", "")
            a2ui_data = response_data.get("a2ui")
            references = response_data.get("references", [])

            # Extract tier and template info from response metadata
            metadata = response_data.get("metadata", {})
            tier = metadata.get("tier")
            template_type = metadata.get("template_type")

            # If A2UI is in v2 format (list), we don't support it - nullify
            if isinstance(a2ui_data, list):
                logger.warning("⚠️ LightRAG returned v2 format A2UI (list) - not supported, nullifying")
                a2ui_data = None

            # Validate A2UI has actual content
            if a2ui_data and isinstance(a2ui_data, dict):
                props = a2ui_data.get("root", {}).get("props", {})
                has_content = False

                for key, value in props.items():
                    if isinstance(value, list) and len(value) > 0:
                        for item in value:
                            if isinstance(item, dict) and any(
                                v for v in item.values() if v and str(v).strip()
                            ):
                                has_content = True
                                break
                        if has_content:
                            break
                    elif isinstance(value, str) and value.strip() and key in ("title", "content", "subtitle"):
                        has_content = True
                        break

                if not has_content:
                    logger.warning("⚠️ A2UI template has no real data - nullifying")
                    a2ui_data = None

            if a2ui_data:
                filled_type = a2ui_data.get("root", {}).get("type", "unknown")
                logger.info(f"✅ RAG+A2UI SUCCESS: Got filled {filled_type} template")
            else:
                logger.info("✅ RAG+A2UI SUCCESS: Text only (no A2UI template filled)")

            logger.info(f"   Response length: {len(text_response)} chars")
            logger.info(f"   References: {len(references)} documents")

            return A2UIResponse(
                text=text_response,
                a2ui=a2ui_data,
                references=references,
                tier=tier,
                template_type=template_type,
                query_time_ms=elapsed_ms,
            )

        except httpx.TimeoutException:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ RAG+A2UI timeout after {elapsed_ms:.1f}ms")
            return A2UIResponse(
                text="I'm having trouble accessing the knowledge base. Please try again.",
                query_time_ms=elapsed_ms,
            )
        except httpx.HTTPStatusError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ RAG+A2UI HTTP error: {e.response.status_code}")
            return A2UIResponse(
                text="I encountered an error while searching the knowledge base.",
                query_time_ms=elapsed_ms,
            )
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ RAG+A2UI error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return A2UIResponse(
                text=f"I encountered an error: {str(e)}",
                query_time_ms=elapsed_ms,
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check if the LightRAG API is healthy.

        Returns:
            Health status dictionary
        """
        try:
            headers = {
                "ngrok-skip-browser-warning": "true",
                "Connection": "keep-alive",
            }
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            # Use shared client for faster health checks
            client = get_shared_client(timeout=10.0, verify=False)
            response = await client.get(
                f"{self.api_url}/health",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"LightRAG health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get the service status."""
        return {
            "type": "lightrag",
            "api_url": self.api_url,
            "mode": self.mode,
            "top_k": self.top_k,
        }

    def update_config(self, config: Dict[str, Any]) -> None:
        """Update the service configuration."""
        self.config.update(config)
        if "api_url" in config:
            self.api_url = config["api_url"]
        if "mode" in config:
            self.mode = config["mode"]
        if "top_k" in config:
            self.top_k = config["top_k"]
        logger.info(f"Updated LightRAG config: {config}")


def create_rag_service(config: Dict[str, Any]) -> BaseRAGService:
    """Factory function to create the appropriate RAG service.

    Args:
        config: Configuration dictionary with 'type' field

    Returns:
        Configured RAG service instance
    """
    rag_type = config.get("type", "mock")
    rag_config = config.get("config", {})

    if rag_type == "lightrag":
        logger.info("Creating LightRAG Service")
        return LightRAGService(config=rag_config)
    else:
        logger.info("Creating Mock RAG Service")
        return RAGService(config=rag_config)
