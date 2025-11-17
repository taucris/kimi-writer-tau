"""
WebSocket-based output handler wrapper.

This module wraps the existing WebSocketManager to implement the OutputHandler interface,
maintaining backward compatibility with the web UI.
"""

from typing import Dict, Any, Optional

from backend.output_handler import OutputHandler
from backend.websocket_manager import WebSocketManager


class WebSocketOutputHandler(OutputHandler):
    """
    WebSocket-based output handler.

    Wraps the existing WebSocketManager to provide backward compatibility
    with the web UI while conforming to the OutputHandler interface.
    """

    def __init__(self, ws_manager: WebSocketManager, project_id: str):
        """
        Initialize the WebSocket output handler.

        Args:
            ws_manager: WebSocket manager instance
            project_id: Project ID for this handler
        """
        self.ws_manager = ws_manager
        self.project_id = project_id

    async def send_phase_change(self, project_id: str, from_phase: str, to_phase: str):
        """Notify clients of phase transition."""
        await self.ws_manager.send_phase_change(project_id, from_phase, to_phase)

    async def send_stream_chunk(self, project_id: str, content: str, is_reasoning: bool = False):
        """Send streaming content chunk."""
        await self.ws_manager.send_stream_chunk(project_id, content, is_reasoning)

    async def send_tool_call(self, project_id: str, tool_name: str, arguments: Dict[str, Any]):
        """Notify clients of tool execution."""
        await self.ws_manager.send_tool_call(project_id, tool_name, arguments)

    async def send_tool_result(self, project_id: str, tool_name: str, result: Dict[str, Any]):
        """Send tool execution result."""
        await self.ws_manager.send_tool_result(project_id, tool_name, result)

    async def send_token_update(self, project_id: str, token_count: int, token_limit: int):
        """Send token usage update."""
        await self.ws_manager.send_token_update(project_id, token_count, token_limit)

    async def request_approval(self, project_id: str, approval_type: str, data: Dict[str, Any]):
        """Request user approval for checkpoint."""
        await self.ws_manager.request_approval(project_id, approval_type, data)

    async def send_progress(
        self,
        project_id: str,
        percentage: float,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Send progress update."""
        await self.ws_manager.send_progress(project_id, percentage, message, details)

    async def send_error(
        self,
        project_id: str,
        error_message: str,
        error_type: Optional[str] = None
    ):
        """Send error notification."""
        await self.ws_manager.send_error(project_id, error_message, error_type)

    async def send_completion(self, project_id: str, stats: Dict[str, Any]):
        """Send novel completion notification."""
        await self.ws_manager.send_completion(project_id, stats)
