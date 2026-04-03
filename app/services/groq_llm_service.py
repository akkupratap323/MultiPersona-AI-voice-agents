"""Groq-compatible LLM service with consecutive user message merging.

Groq's streaming tool-calling is more sensitive than OpenAI's to consecutive
user messages in the context.  When the STT splits a single utterance across
multiple frames (e.g. "The thing is I want to build" + "an agent for my
company"), pipecat's context aggregator appends each as a separate user
message.  Sending those back-to-back to Groq occasionally triggers:

    "Failed to call a function. Please adjust your prompt."

This subclass overrides build_chat_completion_params to merge any consecutive
user messages into a single message before the request leaves the client.  The
merge is purely cosmetic — semantically identical to what the user said —
and only affects the outbound API payload, not the stored context.
"""

from typing import Any, Dict, List, Optional

from loguru import logger
from openai import APIError
from pipecat.services.openai.llm import OpenAILLMService

from pipecat.adapters.services.open_ai_adapter import OpenAILLMInvocationParams


def _merge_consecutive_user_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge consecutive user messages into single messages.

    Only merges messages whose content is a plain string.  Messages with
    structured content (e.g. image payloads represented as lists) are left
    untouched.

    Args:
        messages: List of OpenAI-format message dicts.

    Returns:
        New list with consecutive user messages merged.
    """
    if not messages:
        return messages

    merged: List[Dict[str, Any]] = [messages[0]]

    for msg in messages[1:]:
        prev = merged[-1]
        # Merge only when both are plain-string user messages
        if (
            prev.get("role") == "user"
            and msg.get("role") == "user"
            and isinstance(prev.get("content"), str)
            and isinstance(msg.get("content"), str)
        ):
            prev["content"] = prev["content"].rstrip() + " " + msg["content"].lstrip()
            logger.debug(
                f"Merged consecutive user messages → "
                f"'{prev['content'][:80]}...'"
            )
        else:
            merged.append(msg)

    return merged


class GroqLLMService(OpenAILLMService):
    """OpenAI-compatible LLM service tuned for Groq.

    Identical to OpenAILLMService except that consecutive user messages are
    merged before each API call, preventing the intermittent
    "Failed to call a function" streaming error from Groq.
    """

    def __init__(self, *, model: str = "llama-3.3-70b-versatile", **kwargs):
        # Groq base URL is mandatory; allow caller to override
        kwargs.setdefault("base_url", "https://api.groq.com/openai/v1")
        super().__init__(model=model, **kwargs)

    def build_chat_completion_params(self, params_from_context: OpenAILLMInvocationParams) -> dict:
        """Build params, merging consecutive user messages first."""
        params = super().build_chat_completion_params(params_from_context)

        # Llama models on Groq don't reliably handle parallel tool calls
        if params.get("tools"):
            params["parallel_tool_calls"] = False

        # params["messages"] comes from the context; merge in place
        if "messages" in params:
            original_count = len(params["messages"])
            params["messages"] = _merge_consecutive_user_messages(params["messages"])
            merged_count = len(params["messages"])
            if merged_count < original_count:
                logger.debug(
                    f"merged {original_count - merged_count} consecutive user "
                    f"message(s) before Groq call ({original_count}→{merged_count})"
                )

        return params

    async def _process_context(self, context):
        """Process context with a fallback retry on Groq function-call errors.

        The "Failed to call a function" error from Groq is raised *during
        stream iteration*, not during stream creation.  We wrap the parent
        implementation and, on that specific error, retry the same context
        with tool_choice="none" so the model falls back to a plain text
        response.

        Also handles Llama's 'null' tool call bug — after receiving a tool
        result, Llama sometimes generates a tool call with function name 'null'
        instead of responding with text.
        """
        try:
            await super()._process_context(context)
        except (APIError, Exception) as e:
            error_str = str(e)
            retryable_errors = [
                "Failed to call a function",
                "attempted to call tool 'null'",
                "tool 'null' which was not in request.tools",
            ]
            if not any(err in error_str for err in retryable_errors):
                raise  # Re-raise unrelated errors

            logger.warning(
                f"GroqLLMService: Groq/Llama function-call error during stream "
                f"iteration — retrying with tool_choice=none (error: {error_str[:100]})"
            )
            # Temporarily force tool_choice to "none" for the retry.
            # OpenAILLMContext.tool_choice is a read-only property; use
            # set_tool_choice() which writes the backing _tool_choice field.
            original_tool_choice = context.tool_choice
            context.set_tool_choice("none")
            try:
                await super()._process_context(context)
            finally:
                context.set_tool_choice(original_tool_choice)
