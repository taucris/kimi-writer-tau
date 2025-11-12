"""
Write Critic Agent (Chunk Editor) for Phase 4.

This agent reviews individual chunks for quality, consistency, and adherence
to the plan, either approving them or requesting revisions.
"""

from typing import List

from backend.agents.base_agent import BaseAgent
from backend.tools.base_tool import BaseTool
from backend.tools.write_critique_tools import get_write_critique_tools
from backend.system_prompts import get_custom_prompt_or_default
from backend.config import NovelConfig
from backend.state_manager import NovelState


class WriteCriticAgent(BaseAgent):
    """
    Chunk Editor agent for the write critique phase.

    Responsibilities:
    - Review chunk quality
    - Check adherence to plan
    - Verify character consistency
    - Assess prose quality and pacing
    - Approve chunks or request revisions
    """

    def get_system_prompt(self) -> str:
        """
        Get the write critic agent's system prompt.

        Returns:
            System prompt for write critique phase
        """
        chunk_num = self.state.current_chunk if self.state.current_chunk > 0 else 1
        return get_custom_prompt_or_default(
            'write_critic',
            self.config,
            chunk_num=chunk_num
        )

    def get_tools(self) -> List[BaseTool]:
        """
        Get tools available to the write critic agent.

        Returns:
            List of write critique tools
        """
        return get_write_critique_tools()

    def get_initial_prompt(self) -> str:
        """
        Get the initial prompt to start the chunk critique process.

        Returns:
            Initial user prompt
        """
        chunk_number = self.state.current_chunk if self.state.current_chunk > 0 else 1
        max_iterations = self.config.agent.max_write_critique_iterations

        # Check current iteration
        current_iteration = self.state.chunk_critique_iterations.get(chunk_number, 0)

        return f"""Please review Chunk {chunk_number} for quality and consistency.

Current Critique Iteration: {current_iteration + 1} of {max_iterations}

Your workflow:
1. Use load_chunk_for_review to read Chunk {chunk_number}
2. Use load_context_for_critique to get the plan and previous chunks
3. Carefully evaluate the chunk on multiple dimensions:
   - Adherence to the approved plan and outline
   - Character consistency and development
   - Plot progression and logic
   - Prose quality (dialogue, description, pacing)
   - Continuity with previous chunks
   - Engagement and narrative impact

4. Use critique_chunk to document your assessment
5. Then either:
   - Use approve_chunk if the chunk meets quality standards
   - Use request_revision if significant improvements are needed

Focus on substantive issues rather than minor nitpicks. The goal is to ensure each chunk maintains the quality and consistency of the overall novel.

If this is iteration {max_iterations}, consider being more lenient to prevent infinite revision loops."""
