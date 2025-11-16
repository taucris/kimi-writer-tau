"""
Writing phase tools for the Creative Writer agent.

These tools are used during Phase 3 (WRITING) to write complete chunks
based on the approved plan.
"""

import os
from typing import Dict, Any, Optional

from backend.tools.base_tool import BaseTool
from backend.tools.project import get_active_project_folder
from backend.state_manager import NovelState, save_state, update_phase
from backend.config import Phase


class LoadApprovedPlanTool(BaseTool):
    """Tool for loading the approved plan materials."""

    @property
    def name(self) -> str:
        return "load_approved_plan"

    @property
    def description(self) -> str:
        return """Loads the approved planning materials (summary, characters, structure, outline) \
to refresh your memory before writing. Use this at the start of writing or when you need to check the plan."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def execute(self, state: Optional[NovelState] = None) -> Dict[str, Any]:
        """
        Loads the approved plan.

        Args:
            state: Optional novel state to update

        Returns:
            Tool result dictionary with plan content
        """
        project_folder = get_active_project_folder()
        if not project_folder:
            return {
                "success": False,
                "message": "Error: No active project folder."
            }

        files_to_load = {
            'summary': 'planning/summary.md',
            'characters': 'planning/characters.md',
            'structure': 'planning/structure.md',
            'outline': 'planning/outline.md'
        }

        loaded_content = {}
        for key, rel_path in files_to_load.items():
            file_path = os.path.join(project_folder, rel_path)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        loaded_content[key] = f.read()
                except Exception as e:
                    loaded_content[key] = f"Error reading file: {str(e)}"

        formatted_content = f"""APPROVED PLAN - REFERENCE FOR WRITING:

{'='*80}
{loaded_content.get('summary', 'Summary not found')}

{'='*80}
{loaded_content.get('characters', 'Characters not found')}

{'='*80}
{loaded_content.get('structure', 'Structure not found')}

{'='*80}
{loaded_content.get('outline', 'Outline not found')}

{'='*80}
"""

        return {
            "success": True,
            "message": "Successfully loaded approved plan materials.",
            "content": formatted_content
        }


class GetChunkContextTool(BaseTool):
    """Tool for getting specific context for a chunk."""

    @property
    def name(self) -> str:
        return "get_chunk_context"

    @property
    def description(self) -> str:
        return """Gets the specific outline and context for a particular chunk. \
Use this to see what should happen in the chunk you're about to write."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chunk_number": {
                    "type": "integer",
                    "description": "The chunk number to get context for (1-indexed)"
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
        Gets chunk-specific context.

        Args:
            chunk_number: Chunk number (1-indexed)
            state: Optional novel state to update

        Returns:
            Tool result dictionary with chunk context
        """
        project_folder = get_active_project_folder()
        if not project_folder:
            return {
                "success": False,
                "message": "Error: No active project folder."
            }

        # Load outline
        outline_path = os.path.join(project_folder, "planning", "outline.md")
        if not os.path.exists(outline_path):
            return {
                "success": False,
                "message": "Outline file not found."
            }

        try:
            with open(outline_path, 'r', encoding='utf-8') as f:
                outline_content = f.read()

            # Update state
            if state:
                state.current_chunk = chunk_number
                if chunk_number not in state.chunk_critique_iterations:
                    state.chunk_critique_iterations[chunk_number] = 0
                save_state(state)

            return {
                "success": True,
                "message": f"Context loaded for Chunk {chunk_number}",
                "content": f"""CHUNK {chunk_number} CONTEXT:

Full outline for reference:
{outline_content}

NOTE: Focus on the section for Chunk {chunk_number} when writing.
""",
                "chunk_number": chunk_number
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error loading context: {str(e)}"
            }


class WriteChunkTool(BaseTool):
    """Tool for writing a complete chunk."""

    @property
    def name(self) -> str:
        return "write_chunk"

    @property
    def description(self) -> str:
        return """Writes a complete chunk to a file. The chunk should be substantial (2,500-5,000+ words), \
fully developed with scenes, dialogue, and description. Creates the file in the manuscript directory."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chunk_number": {
                    "type": "integer",
                    "description": "The chunk number (used for filename)"
                },
                "content": {
                    "type": "string",
                    "description": "The complete chunk content"
                }
            },
            "required": ["chunk_number", "content"]
        }

    def execute(
        self,
        chunk_number: int,
        content: str,
        state: Optional[NovelState] = None
    ) -> Dict[str, Any]:
        """
        Writes a chunk file.

        Args:
            chunk_number: Chunk number
            content: Chunk content
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

        # Format chunk filename
        filename = f"chunk_{chunk_number:02d}.md"
        file_path = os.path.join(project_folder, "manuscript", filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Chunk {chunk_number}\n\n")
                f.write(content)
                f.write("\n")

            word_count = len(content.split())

            return {
                "success": True,
                "message": f"Successfully wrote Chunk {chunk_number} ({word_count} words) to manuscript/{filename}",
                "file_path": file_path,
                "filename": filename,
                "chunk_number": chunk_number,
                "word_count": word_count,
                "next_step": "Use finalize_chunk to submit this chunk for critique"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error writing chunk: {str(e)}"
            }


class ReviewPreviousWritingTool(BaseTool):
    """Tool for reviewing previously written chunks."""

    @property
    def name(self) -> str:
        return "review_previous_writing"

    @property
    def description(self) -> str:
        return """Loads and displays previously written chunks for continuity checking. \
Use this to maintain consistency in voice, plot, and character development."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chunk_range": {
                    "type": "string",
                    "description": "Chunk range to review (e.g., '1-3' or 'all' or '5')"
                }
            },
            "required": ["chunk_range"]
        }

    def execute(
        self,
        chunk_range: str,
        state: Optional[NovelState] = None
    ) -> Dict[str, Any]:
        """
        Reviews previous chunks.

        Args:
            chunk_range: Chunk range specification
            state: Optional novel state to update

        Returns:
            Tool result dictionary with previous chunks
        """
        project_folder = get_active_project_folder()
        if not project_folder:
            return {
                "success": False,
                "message": "Error: No active project folder."
            }

        manuscript_dir = os.path.join(project_folder, "manuscript")
        if not os.path.exists(manuscript_dir):
            return {
                "success": False,
                "message": "No manuscript directory found. No chunks written yet."
            }

        # Parse chunk range
        chunks_to_load = []
        if chunk_range.lower() == 'all':
            # Load all chunks
            for file in sorted(os.listdir(manuscript_dir)):
                if file.startswith('chunk_') and file.endswith('.md'):
                    chunks_to_load.append(file)
        elif '-' in chunk_range:
            # Range like "1-3"
            try:
                start, end = map(int, chunk_range.split('-'))
                for i in range(start, end + 1):
                    chunks_to_load.append(f"chunk_{i:02d}.md")
            except:
                return {
                    "success": False,
                    "message": f"Invalid chunk range format: {chunk_range}"
                }
        else:
            # Single chunk
            try:
                num = int(chunk_range)
                chunks_to_load.append(f"chunk_{num:02d}.md")
            except:
                return {
                    "success": False,
                    "message": f"Invalid chunk number: {chunk_range}"
                }

        # Load chunks
        loaded_chunks = []
        for filename in chunks_to_load:
            file_path = os.path.join(manuscript_dir, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        loaded_chunks.append(f"\n{'='*80}\n{filename}\n{'='*80}\n{content}")
                except Exception as e:
                    loaded_chunks.append(f"\nError loading {filename}: {str(e)}")

        if not loaded_chunks:
            return {
                "success": False,
                "message": f"No chunks found for range: {chunk_range}"
            }

        formatted_content = f"""PREVIOUS CHUNKS FOR REVIEW:

{''.join(loaded_chunks)}

{'='*80}
END OF PREVIOUS CHUNKS
{'='*80}
"""

        return {
            "success": True,
            "message": f"Loaded {len(loaded_chunks)} chunk(s) for review.",
            "content": formatted_content,
            "chunks_loaded": len(loaded_chunks)
        }


class FinalizeChunkTool(BaseTool):
    """Tool for finalizing a chunk and submitting for critique."""

    @property
    def name(self) -> str:
        return "finalize_chunk"

    @property
    def description(self) -> str:
        return """Finalizes a chunk and submits it for critique. Call this after writing a complete chunk. \
This transitions to the write critique phase for this specific chunk."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chunk_number": {
                    "type": "integer",
                    "description": "The chunk number being finalized"
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes about the chunk"
                }
            },
            "required": ["chunk_number"]
        }

    def execute(
        self,
        chunk_number: int,
        notes: str = "",
        state: Optional[NovelState] = None
    ) -> Dict[str, Any]:
        """
        Finalizes a chunk.

        Args:
            chunk_number: Chunk number
            notes: Optional notes
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

        # Verify chunk exists
        filename = f"chunk_{chunk_number:02d}.md"
        file_path = os.path.join(project_folder, "manuscript", filename)

        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"Chunk {chunk_number} not found. Write the chunk first using write_chunk."
            }

        # Update state
        if state:
            update_phase(state, Phase.WRITE_CRITIQUE)
            state.current_chunk = chunk_number
            save_state(state)

        return {
            "success": True,
            "message": f"Chunk {chunk_number} finalized and submitted for critique.",
            "transition": {
                "to_phase": "WRITE_CRITIQUE",
                "data": {
                    "chunk_number": chunk_number,
                    "notes": notes
                }
            },
            "next_phase": f"The Chunk Editor will now review Chunk {chunk_number}."
        }


# Registry of all writing tools
def get_writing_tools():
    """Get all writing phase tools."""
    return [
        LoadApprovedPlanTool(),
        GetChunkContextTool(),
        WriteChunkTool(),
        ReviewPreviousWritingTool(),
        FinalizeChunkTool()
    ]
