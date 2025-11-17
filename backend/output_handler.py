"""
Output handler abstraction for the Kimi Novel Writing System.

This module provides an abstract interface for generation output,
supporting both WebSocket (web UI) and console (terminal UI) modes.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class OutputHandler(ABC):
    """
    Abstract interface for generation output.

    Implementations can output to WebSocket, console, or any other medium.
    """

    @abstractmethod
    async def send_phase_change(self, project_id: str, from_phase: str, to_phase: str):
        """
        Notify of phase transition.

        Args:
            project_id: Project ID
            from_phase: Previous phase
            to_phase: New phase
        """
        pass

    @abstractmethod
    async def send_stream_chunk(self, project_id: str, content: str, is_reasoning: bool = False):
        """
        Send streaming content chunk.

        Args:
            project_id: Project ID
            content: Content chunk
            is_reasoning: Whether this is reasoning content
        """
        pass

    @abstractmethod
    async def send_tool_call(self, project_id: str, tool_name: str, arguments: Dict[str, Any]):
        """
        Notify of tool execution.

        Args:
            project_id: Project ID
            tool_name: Name of tool being called
            arguments: Tool arguments
        """
        pass

    @abstractmethod
    async def send_tool_result(self, project_id: str, tool_name: str, result: Dict[str, Any]):
        """
        Send tool execution result.

        Args:
            project_id: Project ID
            tool_name: Name of tool
            result: Tool result
        """
        pass

    @abstractmethod
    async def send_token_update(self, project_id: str, token_count: int, token_limit: int):
        """
        Send token usage update.

        Args:
            project_id: Project ID
            token_count: Current token count
            token_limit: Maximum token limit
        """
        pass

    @abstractmethod
    async def request_approval(self, project_id: str, approval_type: str, data: Dict[str, Any]):
        """
        Request user approval for checkpoint.

        Args:
            project_id: Project ID
            approval_type: Type of approval needed
            data: Additional data for approval
        """
        pass

    @abstractmethod
    async def send_progress(
        self,
        project_id: str,
        percentage: float,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Send progress update.

        Args:
            project_id: Project ID
            percentage: Progress percentage (0-100)
            message: Progress message
            details: Optional additional details
        """
        pass

    @abstractmethod
    async def send_error(
        self,
        project_id: str,
        error_message: str,
        error_type: Optional[str] = None
    ):
        """
        Send error notification.

        Args:
            project_id: Project ID
            error_message: Error message
            error_type: Optional error type/category
        """
        pass

    @abstractmethod
    async def send_completion(self, project_id: str, stats: Dict[str, Any]):
        """
        Send novel completion notification.

        Args:
            project_id: Project ID
            stats: Generation statistics
        """
        pass
