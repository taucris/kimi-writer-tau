"""
DeepInfra model provider implementation.

This module implements the DeepInfra provider for GLM and other models.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
import logging

from backend.model_providers.base_provider import BaseModelProvider

logger = logging.getLogger(__name__)


class DeepInfraProvider(BaseModelProvider):
    """
    Provider implementation for DeepInfra.

    Uses OpenAI SDK with DeepInfra's OpenAI-compatible endpoint.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepinfra.com/v1/openai",
        **kwargs
    ):
        """
        Initialize DeepInfra provider.

        Args:
            api_key: DeepInfra API token
            base_url: Base URL for DeepInfra API
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.base_url = base_url
        self.initialize_client()

    def get_base_url(self) -> str:
        """Get the base URL for API calls."""
        return self.base_url

    def initialize_client(self):
        """Initialize the OpenAI client configured for DeepInfra."""
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        logger.info(f"Initialized DeepInfra provider with base URL: {self.base_url}")

    def format_messages(
        self,
        messages: List[Dict[str, Any]],
        model_id: str
    ) -> List[Dict[str, Any]]:
        """
        Format messages for DeepInfra models.

        Some models may need special formatting. For now, we handle:
        - Remove reasoning_content from messages as it's Kimi-specific
        - Ensure content is always a string (not None)

        Args:
            messages: List of message dictionaries
            model_id: Model identifier

        Returns:
            Formatted messages
        """
        formatted = []

        for msg in messages:
            formatted_msg = msg.copy()

            # Remove reasoning_content if present (Kimi-specific)
            if 'reasoning_content' in formatted_msg:
                del formatted_msg['reasoning_content']

            # Ensure content is string or not present (some messages like tool calls may not have content)
            if 'content' in formatted_msg and formatted_msg['content'] is None:
                # For assistant messages with tool calls, content can be None or empty string
                if formatted_msg.get('role') == 'assistant' and formatted_msg.get('tool_calls'):
                    formatted_msg['content'] = ''
                else:
                    # For other messages, if content is None, skip it
                    del formatted_msg['content']

            formatted.append(formatted_msg)

        return formatted

    def create_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 1.0,
        stream: bool = False,
        timeout: float = 120.0,
        **kwargs
    ) -> Any:
        """
        Create a chat completion request with DeepInfra.

        Args:
            model: Model identifier (e.g., 'zai-org/GLM-4.6')
            messages: Conversation messages
            tools: Tool definitions
            temperature: Sampling temperature
            stream: Whether to stream the response
            timeout: Request timeout
            **kwargs: Additional parameters

        Returns:
            OpenAI chat completion response
        """
        # Format messages for DeepInfra
        formatted_messages = self.format_messages(messages, model)

        # Create completion
        return self._client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            tools=tools,
            temperature=temperature,
            stream=stream,
            timeout=timeout,
            **kwargs
        )

    def parse_stream_chunk(self, chunk: Any) -> Dict[str, Any]:
        """
        Parse a streaming response chunk from DeepInfra.

        Args:
            chunk: Raw chunk from streaming response

        Returns:
            Parsed chunk dictionary
        """
        result = {
            'role': None,
            'reasoning_content': None,
            'content': None,
            'tool_calls': None
        }

        if not chunk.choices:
            return result

        delta = chunk.choices[0].delta

        # Extract role
        if hasattr(delta, "role") and delta.role:
            result['role'] = delta.role

        # DeepInfra models typically don't have reasoning_content
        # (that's a Kimi-specific feature)

        # Extract regular content
        if hasattr(delta, "content") and delta.content:
            result['content'] = delta.content

        # Extract tool calls
        if hasattr(delta, "tool_calls") and delta.tool_calls:
            result['tool_calls'] = delta.tool_calls

        return result

    def supports_reasoning(self, model_id: str) -> bool:
        """
        Check if model supports reasoning output.

        Most DeepInfra models don't have explicit reasoning output like Kimi.

        Args:
            model_id: Model identifier

        Returns:
            False (most DeepInfra models don't support reasoning output)
        """
        # Could be extended in the future if specific models support it
        return False

    def supports_tools(self, model_id: str) -> bool:
        """
        Check if model supports tools.

        GLM-4.6 supports tool calling according to documentation.

        Args:
            model_id: Model identifier

        Returns:
            True for GLM models and other supported models
        """
        # GLM-4.6 supports tools according to the documentation
        if 'glm' in model_id.lower():
            return True

        # Default to True for other models (can be refined later)
        return True

    def get_context_window(self, model_id: str) -> int:
        """
        Get context window size for model.

        Args:
            model_id: Model identifier

        Returns:
            Context window size in tokens
        """
        # GLM-4.6 has 200K context window according to documentation
        if 'glm-4.6' in model_id.lower():
            return 200000

        # Default
        return 200000
