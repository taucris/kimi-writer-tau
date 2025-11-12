"""
Moonshot AI model provider implementation.

This module implements the Moonshot AI provider for Kimi models.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
import logging

from backend.model_providers.base_provider import BaseModelProvider

logger = logging.getLogger(__name__)


class MoonshotProvider(BaseModelProvider):
    """
    Provider implementation for Moonshot AI (Kimi models).

    Uses OpenAI SDK with Moonshot's base URL.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.moonshot.ai/v1", **kwargs):
        """
        Initialize Moonshot provider.

        Args:
            api_key: Moonshot API key
            base_url: Base URL for Moonshot API (default: https://api.moonshot.ai/v1)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.base_url = base_url
        self.initialize_client()

    def get_base_url(self) -> str:
        """Get the base URL for API calls."""
        return self.base_url

    def initialize_client(self):
        """Initialize the OpenAI client configured for Moonshot."""
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        logger.info(f"Initialized Moonshot provider with base URL: {self.base_url}")

    def format_messages(
        self,
        messages: List[Dict[str, Any]],
        model_id: str
    ) -> List[Dict[str, Any]]:
        """
        Format messages for Moonshot models.

        Moonshot uses standard OpenAI message format, no special formatting needed.

        Args:
            messages: List of message dictionaries
            model_id: Model identifier

        Returns:
            Messages (unchanged for Moonshot)
        """
        return messages

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
        Create a chat completion request with Moonshot.

        Args:
            model: Model identifier (e.g., 'kimi-k2-thinking')
            messages: Conversation messages
            tools: Tool definitions
            temperature: Sampling temperature
            stream: Whether to stream the response
            timeout: Request timeout
            **kwargs: Additional parameters

        Returns:
            OpenAI chat completion response
        """
        # Format messages if needed
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
        Parse a streaming response chunk from Moonshot.

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

        # Extract reasoning content (Kimi-specific)
        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
            result['reasoning_content'] = delta.reasoning_content

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

        Kimi K2 Thinking supports reasoning output.

        Args:
            model_id: Model identifier

        Returns:
            True if model supports reasoning
        """
        return 'thinking' in model_id.lower() or 'k2' in model_id.lower()

    def supports_tools(self, model_id: str) -> bool:
        """Check if model supports tools."""
        return True

    def get_context_window(self, model_id: str) -> int:
        """Get context window size."""
        return 200000  # Kimi K2 Thinking has 200K context window
