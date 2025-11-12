"""
Base model provider class.

This module defines the abstract interface that all model providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator, Optional
import logging

logger = logging.getLogger(__name__)


class BaseModelProvider(ABC):
    """
    Abstract base class for AI model providers.

    Each provider (Moonshot, DeepInfra, etc.) must implement this interface
    to ensure compatibility with the agent loop.
    """

    def __init__(self, api_key: str, **kwargs):
        """
        Initialize the provider.

        Args:
            api_key: API key for authentication
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
        self._client = None

    @abstractmethod
    def get_base_url(self) -> str:
        """
        Get the base URL for API calls.

        Returns:
            Base URL string
        """
        pass

    @abstractmethod
    def initialize_client(self):
        """
        Initialize the API client.

        This method should create and configure the HTTP client for API calls.
        """
        pass

    @abstractmethod
    def format_messages(
        self,
        messages: List[Dict[str, Any]],
        model_id: str
    ) -> List[Dict[str, Any]]:
        """
        Format messages for the specific model's requirements.

        Some models may require different message structures or preprocessing.

        Args:
            messages: List of message dictionaries
            model_id: Model identifier

        Returns:
            Formatted messages list
        """
        pass

    @abstractmethod
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
        Create a chat completion request.

        Args:
            model: Model identifier
            messages: Conversation messages
            tools: Tool definitions (for function calling)
            temperature: Sampling temperature
            stream: Whether to stream the response
            timeout: Request timeout in seconds
            **kwargs: Additional provider-specific parameters

        Returns:
            Response object (format varies by provider)
        """
        pass

    @abstractmethod
    def parse_stream_chunk(self, chunk: Any) -> Dict[str, Any]:
        """
        Parse a streaming response chunk.

        Args:
            chunk: Raw chunk from streaming response

        Returns:
            Parsed chunk dictionary with keys:
                - role: Message role (if present)
                - reasoning_content: Reasoning text (if present)
                - content: Regular content text (if present)
                - tool_calls: Tool call data (if present)
        """
        pass

    def supports_reasoning(self, model_id: str) -> bool:
        """
        Check if a model supports reasoning output.

        Args:
            model_id: Model identifier

        Returns:
            True if model supports reasoning, False otherwise
        """
        return False

    def supports_tools(self, model_id: str) -> bool:
        """
        Check if a model supports tool/function calling.

        Args:
            model_id: Model identifier

        Returns:
            True if model supports tools, False otherwise
        """
        return True

    def get_context_window(self, model_id: str) -> int:
        """
        Get the context window size for a model.

        Args:
            model_id: Model identifier

        Returns:
            Context window size in tokens
        """
        return 200000  # Default

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(base_url={self.get_base_url()})"
