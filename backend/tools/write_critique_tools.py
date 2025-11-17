"""
Write critique phase tools for the Chunk Editor agent.

These tools are used during Phase 4 (WRITE_CRITIQUE) to review and critique
individual chunks, ensuring quality before moving forward.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

from backend.tools.base_tool import BaseTool
from backend.tools.project import get_active_project_folder
from backend.state_manager import NovelState, save_state, update_phase, increment_chunk
from backend.config import Phase


class LoadChunkForReviewTool(BaseTool):
    """Tool for loading a chunk for review."""

    @property
    def name(self) -> str:
        return "load_chunk_for_review"

    @property
    def description(self) -> str:
        return """Loads the specified chunk for review. Use this to read the chunk content \
before providing critique."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chunk_number": {
                    "type": "integer",
                    "description": "The chunk number to review (1-indexed)"
                }
            },
            "required": ["chunk_number"]
        }

    def execute(
        self,
        chunk_number: int,
        state: Optional[NovelState] = None
    ) -> Dict[str, Any]:
        """
        Loads a chunk for review.

        Args:
            chunk_number: Chunk number to load
            state: Optional novel state to update

        Returns:
            Tool result dictionary with chunk content
        """
        project_folder = get_active_project_folder()
        if not project_folder:
            return {
                "success": False,
                "message": "Error: No active project folder."
            }

        filename = f"chunk_{chunk_number:02d}.md"
        file_path = os.path.join(project_folder, "manuscript", filename)

        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"Chunk {chunk_number} not found."
            }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            word_count = len(content.split())

            formatted_content = f"""CHUNK {chunk_number} FOR REVIEW:

{'='*80}
{content}
{'='*80}

Word Count: {word_count}
"""

            return {
                "success": True,
                "message": f"Loaded Chunk {chunk_number} for review ({word_count} words).",
                "content": formatted_content,
                "chunk_number": chunk_number,
                "word_count": word_count
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error loading chunk: {str(e)}"
            }


class LoadContextForCritiqueTool(BaseTool):
    """Tool for loading relevant context for chunk critique."""

    @property
    def name(self) -> str:
        return "load_context_for_critique"

    @property
    def description(self) -> str:
        return """Loads relevant context for critiquing a chunk, including the plan, outline, \
and previous chunks for continuity checking."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chunk_number": {
                    "type": "integer",
                    "description": "The chunk number being critiqued"
                }
            },
            "required": ["chunk_number"]
        }

    def execute(
        self,
        chunk_number: int,
        state: Optional[NovelState] = None
    ) -> Dict[str, Any]:
        """
        Loads context for critique.

        Args:
            chunk_number: Chunk number being critiqued
            state: Optional novel state to update

        Returns:
            Tool result dictionary with context
        """
        project_folder = get_active_project_folder()
        if not project_folder:
            return {
                "success": False,
                "message": "Error: No active project folder."
            }

        context_parts = []

        # Load outline
        outline_path = os.path.join(project_folder, "planning", "outline.md")
        if os.path.exists(outline_path):
            try:
                with open(outline_path, 'r', encoding='utf-8') as f:
                    outline = f.read()
                    context_parts.append(f"PLOT OUTLINE:\n{'='*80}\n{outline}")
            except:
                pass

        # Load character profiles
        chars_path = os.path.join(project_folder, "planning", "characters.md")
        if os.path.exists(chars_path):
            try:
                with open(chars_path, 'r', encoding='utf-8') as f:
                    chars = f.read()
                    context_parts.append(f"\nCHARACTER PROFILES:\n{'='*80}\n{chars}")
            except:
                pass

        # Load previous chunk if exists
        if chunk_number > 1:
            prev_filename = f"chunk_{chunk_number-1:02d}.md"
            prev_path = os.path.join(project_folder, "manuscript", prev_filename)
            if os.path.exists(prev_path):
                try:
                    with open(prev_path, 'r', encoding='utf-8') as f:
                        prev_chunk = f.read()
                        context_parts.append(f"\nPREVIOUS CHUNK (Chunk {chunk_number-1}):\n{'='*80}\n{prev_chunk}")
                except:
                    pass

        formatted_content = f"""CONTEXT FOR CRITIQUING CHUNK {chunk_number}:

{'='*80}
{''.join(context_parts)}
{'='*80}
"""

        return {
            "success": True,
            "message": f"Loaded context for critiquing Chunk {chunk_number}.",
            "content": formatted_content
        }


class CritiqueChunkTool(BaseTool):
    """Tool for providing critique feedback on a chunk."""

    @property
    def name(self) -> str:
        return "critique_chunk"

    @property
    def description(self) -> str:
        return """Provides detailed critique of a chunk. Document issues with plot consistency, \
character behavior, prose quality, pacing, or adherence to the plan. This critique will be saved."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chunk_number": {
                    "type": "integer",
                    "description": "The chunk number being critiqued"
                },
                "critique_text": {
                    "type": "string",
                    "description": "Detailed critique feedback"
                }
            },
            "required": ["chunk_number", "critique_text"]
        }

    def execute(
        self,
        chunk_number: int,
        critique_text: str,
        state: Optional[NovelState] = None
    ) -> Dict[str, Any]:
        """
        Saves chunk critique.

        Args:
            chunk_number: Chunk number
            critique_text: Critique feedback
            state: Optional novel state to update

        Returns:
            Tool result dictionary
        """
        project_folder = get_active_project_folder()
        if not project_folder:
            return {
                "success": False,
                "message": "Error: No active project folder."
            }

        # Determine critique version
        version = 1
        if state and chunk_number in state.chunk_critique_iterations:
            version = state.chunk_critique_iterations[chunk_number] + 1
            state.chunk_critique_iterations[chunk_number] = version
        elif state:
            state.chunk_critique_iterations[chunk_number] = 1

        # Save critique
        critique_dir = os.path.join(project_folder, "critiques")
        os.makedirs(critique_dir, exist_ok=True)

        filename = f"chunk_{chunk_number:02d}_critique_v{version}.md"
        file_path = os.path.join(critique_dir, filename)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Chunk {chunk_number} Critique - Version {version}\n\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"---\n\n")
                f.write(critique_text)
                f.write("\n")

            if state:
                save_state(state)

            return {
                "success": True,
                "message": f"Critique saved for Chunk {chunk_number} (version {version}).",
                "file_path": file_path,
                "version": version,
                "chunk_number": chunk_number,
                "next_step": "Use approve_chunk to accept it or request_revision to send back for improvements"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error saving critique: {str(e)}"
            }


class ApproveChunkTool(BaseTool):
    """Tool for approving a chunk and moving to next chunk or completion."""

    @property
    def name(self) -> str:
        return "approve_chunk"

    @property
    def description(self) -> str:
        return """Approves a chunk, marking it as complete. If there are more chunks to write, \
transitions back to writing phase for the next chunk. If this is the last chunk, completes the novel."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chunk_number": {
                    "type": "integer",
                    "description": "The chunk number being approved"
                },
                "approval_notes": {
                    "type": "string",
                    "description": "Notes about why the chunk is approved"
                }
            },
            "required": ["chunk_number", "approval_notes"]
        }

    def execute(
        self,
        chunk_number: int,
        approval_notes: str,
        state: Optional[NovelState] = None
    ) -> Dict[str, Any]:
        """
        Approves a chunk.

        Args:
            chunk_number: Chunk number
            approval_notes: Approval notes
            state: Optional novel state to update

        Returns:
            Tool result dictionary with transition information
        """
        project_folder = get_active_project_folder()
        if not project_folder:
            return {
                "success": False,
                "message": "Error: No active project folder."
            }

        # Save approval notes
        approval_dir = os.path.join(project_folder, "critiques")
        os.makedirs(approval_dir, exist_ok=True)

        filename = f"chunk_{chunk_number:02d}_approval.md"
        file_path = os.path.join(approval_dir, filename)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Chunk {chunk_number} Approval\n\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**Status:** APPROVED\n\n")
                f.write(f"---\n\n")
                f.write(approval_notes)
                f.write("\n")

            # Update state (but don't change phase yet - let agent_loop handle that)
            is_complete = False
            next_phase_msg = ""

            if state:
                # Mark chunk as completed and approved
                if chunk_number not in state.chunks_completed:
                    state.chunks_completed.append(chunk_number)
                if chunk_number not in state.chunks_approved:
                    state.chunks_approved.append(chunk_number)

                # Check if novel is complete
                if len(state.chunks_approved) >= state.total_chunks:
                    is_complete = True
                    next_phase_msg = "All chunks complete! Novel generation finished (pending user approval if enabled)."
                else:
                    # Move to next chunk (increment counter but don't change phase)
                    increment_chunk(state)
                    next_phase_msg = f"Chunk {chunk_number} approved by critic. Moving to Chunk {state.current_chunk} (pending user approval if enabled)."

                save_state(state)

            return {
                "success": True,
                "message": f"Chunk {chunk_number} approved by critic!",
                "file_path": file_path,
                "is_complete": is_complete,
                "transition": {
                    "to_phase": "COMPLETE" if is_complete else "WRITING",
                    "data": {
                        "chunk_number": chunk_number,
                        "approval_notes": approval_notes,
                        "next_chunk": state.current_chunk if state and not is_complete else None
                    }
                },
                "next_phase": next_phase_msg
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error approving chunk: {str(e)}"
            }


class RequestRevisionTool(BaseTool):
    """Tool for requesting revisions to a chunk."""

    @property
    def name(self) -> str:
        return "request_revision"

    @property
    def description(self) -> str:
        return """Requests revisions to a chunk. Sends the chunk back to the writing phase \
with specific revision notes. The writer will revise and resubmit the chunk."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chunk_number": {
                    "type": "integer",
                    "description": "The chunk number requiring revision"
                },
                "revision_notes": {
                    "type": "string",
                    "description": "Specific notes about what needs to be revised"
                }
            },
            "required": ["chunk_number", "revision_notes"]
        }

    def execute(
        self,
        chunk_number: int,
        revision_notes: str,
        state: Optional[NovelState] = None
    ) -> Dict[str, Any]:
        """
        Requests chunk revision.

        Args:
            chunk_number: Chunk number
            revision_notes: Revision requirements
            state: Optional novel state to update

        Returns:
            Tool result dictionary with transition information
        """
        project_folder = get_active_project_folder()
        if not project_folder:
            return {
                "success": False,
                "message": "Error: No active project folder."
            }

        # Check iteration limit
        if state:
            max_iterations = 2  # Default, should come from config
            current_iterations = state.chunk_critique_iterations.get(chunk_number, 0)

            if current_iterations >= max_iterations:
                return {
                    "success": False,
                    "message": f"Maximum critique iterations ({max_iterations}) reached for Chunk {chunk_number}. Auto-approving to prevent infinite loop.",
                    "auto_approve": True
                }

        # Save revision request
        revision_dir = os.path.join(project_folder, "critiques")
        os.makedirs(revision_dir, exist_ok=True)

        version = state.chunk_critique_iterations.get(chunk_number, 0) if state else 0
        filename = f"chunk_{chunk_number:02d}_revision_request_v{version}.md"
        file_path = os.path.join(revision_dir, filename)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Chunk {chunk_number} Revision Request - Version {version}\n\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**Status:** REVISION REQUESTED\n\n")
                f.write(f"---\n\n")
                f.write(revision_notes)
                f.write("\n")

            # Update state - transition back to writing
            if state:
                update_phase(state, Phase.WRITING)
                save_state(state)

            return {
                "success": True,
                "message": f"Revision requested for Chunk {chunk_number}. Transitioning back to writing phase.",
                "file_path": file_path,
                "transition": {
                    "to_phase": "WRITING",
                    "data": {
                        "chunk_number": chunk_number,
                        "revision_notes": revision_notes,
                        "iteration": version
                    }
                },
                "next_phase": f"The Creative Writer will now revise Chunk {chunk_number} based on feedback."
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error requesting revision: {str(e)}"
            }


# Registry of all write critique tools
def get_write_critique_tools():
    """Get all write critique phase tools."""
    return [
        LoadChunkForReviewTool(),
        LoadContextForCritiqueTool(),
        CritiqueChunkTool(),
        ApproveChunkTool(),
        RequestRevisionTool()
    ]
