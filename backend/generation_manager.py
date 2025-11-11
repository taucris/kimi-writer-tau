"""
Background task manager for novel generation.

This module manages active generation tasks, allowing projects to run
in the background while handling pause/resume and completion.
"""

import asyncio
import logging
from typing import Dict, Optional
from backend.agent_loop import AgentLoop

logger = logging.getLogger(__name__)


class GenerationManager:
    """
    Manages background generation tasks for multiple projects.

    Tracks active generation loops and provides methods to start,
    stop, and check status of generation tasks.
    """

    def __init__(self):
        """Initialize the generation manager."""
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.active_loops: Dict[str, AgentLoop] = {}

    def is_running(self, project_id: str) -> bool:
        """
        Check if a project has an active generation task.

        Args:
            project_id: Project ID to check

        Returns:
            True if generation is running for this project
        """
        task = self.active_tasks.get(project_id)
        if task and not task.done():
            return True
        return False

    async def start_generation(self, project_id: str) -> bool:
        """
        Start generation for a project.

        Args:
            project_id: Project ID to start generation for

        Returns:
            True if started successfully, False if already running
        """
        # Check if already running
        if self.is_running(project_id):
            logger.warning(f"Generation already running for project {project_id}")
            return False

        # Create agent loop
        try:
            agent_loop = AgentLoop(project_id)
            self.active_loops[project_id] = agent_loop

            # Start generation as background task
            task = asyncio.create_task(self._run_with_cleanup(project_id, agent_loop))
            self.active_tasks[project_id] = task

            logger.info(f"Started generation for project {project_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start generation for project {project_id}: {e}")
            raise

    async def _run_with_cleanup(self, project_id: str, agent_loop: AgentLoop):
        """
        Run agent loop with automatic cleanup on completion or error.

        Args:
            project_id: Project ID
            agent_loop: Agent loop instance
        """
        try:
            await agent_loop.run()
            logger.info(f"Generation completed for project {project_id}")
        except Exception as e:
            logger.error(f"Generation error for project {project_id}: {e}", exc_info=True)
        finally:
            # Cleanup
            if project_id in self.active_tasks:
                del self.active_tasks[project_id]
            if project_id in self.active_loops:
                del self.active_loops[project_id]
            logger.info(f"Cleaned up generation task for project {project_id}")

    def stop_generation(self, project_id: str) -> bool:
        """
        Stop generation for a project.

        Note: This cancels the task. Use pause/resume to temporarily pause.

        Args:
            project_id: Project ID to stop generation for

        Returns:
            True if stopped successfully, False if not running
        """
        task = self.active_tasks.get(project_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled generation task for project {project_id}")
            return True
        return False

    def get_active_projects(self) -> list[str]:
        """
        Get list of projects with active generation.

        Returns:
            List of project IDs with active generation
        """
        return [
            project_id for project_id, task in self.active_tasks.items()
            if not task.done()
        ]

    def get_loop(self, project_id: str) -> Optional[AgentLoop]:
        """
        Get the agent loop for a project.

        Args:
            project_id: Project ID

        Returns:
            AgentLoop instance if running, None otherwise
        """
        return self.active_loops.get(project_id)


# Global generation manager instance
_generation_manager: Optional[GenerationManager] = None


def get_generation_manager() -> GenerationManager:
    """
    Get the global generation manager instance.

    Returns:
        GenerationManager singleton instance
    """
    global _generation_manager
    if _generation_manager is None:
        _generation_manager = GenerationManager()
    return _generation_manager
