"""
Conversation history persistence for robust checkpointing and recovery.

This module handles saving and loading agent conversation history to enable
recovery from interruptions (user-initiated or errors).
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def get_conversation_history_path(project_id: str, phase: str) -> str:
    """
    Get path to conversation history file.

    Args:
        project_id: Project ID
        phase: Current phase (e.g., "PLANNING", "WRITING")

    Returns:
        Path to conversation history file
    """
    return f"output/{project_id}/.conversation_history_{phase}.json"


def get_conversation_log_path(project_id: str, phase: str) -> str:
    """
    Get path to human-readable conversation log.

    Args:
        project_id: Project ID
        phase: Current phase

    Returns:
        Path to conversation log file
    """
    return f"output/{project_id}/.conversation_log_{phase}.md"


def serialize_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize a message to ensure all fields are JSON-compatible.

    Args:
        message: Message dictionary (may contain objects)

    Returns:
        Serialized message dictionary
    """
    serialized = {}

    if 'role' in message:
        serialized['role'] = message['role']

    if 'content' in message:
        serialized['content'] = message['content']

    if 'name' in message:
        serialized['name'] = message['name']

    if 'tool_call_id' in message:
        serialized['tool_call_id'] = message['tool_call_id']

    # Handle tool_calls - convert objects to dicts
    if 'tool_calls' in message and message['tool_calls']:
        serialized_tool_calls = []
        for tc in message['tool_calls']:
            if isinstance(tc, dict):
                serialized_tool_calls.append(tc)
            elif hasattr(tc, '__dict__'):
                # Convert object to dict
                tc_dict = {
                    'id': getattr(tc, 'id', None),
                    'type': getattr(tc, 'type', 'function'),
                    'function': {
                        'name': getattr(tc.function, 'name', '') if hasattr(tc, 'function') else '',
                        'arguments': getattr(tc.function, 'arguments', '') if hasattr(tc, 'function') else ''
                    }
                }
                serialized_tool_calls.append(tc_dict)
        serialized['tool_calls'] = serialized_tool_calls

    # Include reasoning content if present (for kimi-k2-thinking model)
    if 'reasoning_content' in message:
        serialized['reasoning_content'] = message['reasoning_content']

    return serialized


def save_conversation_history(
    project_id: str,
    phase: str,
    messages: List[Dict[str, Any]],
    iteration: int
) -> None:
    """
    Save conversation history to file.

    Args:
        project_id: Project ID
        phase: Current phase
        messages: List of message dictionaries
        iteration: Current iteration number
    """
    history_path = get_conversation_history_path(project_id, phase)

    # Serialize all messages
    serialized_messages = [serialize_message(msg) for msg in messages]

    # Create history data with metadata
    history_data = {
        'project_id': project_id,
        'phase': phase,
        'iteration': iteration,
        'timestamp': datetime.now().isoformat(),
        'message_count': len(serialized_messages),
        'messages': serialized_messages
    }

    # Ensure directory exists
    os.makedirs(os.path.dirname(history_path), exist_ok=True)

    # Write with backup
    _write_with_backup(history_path, history_data)

    logger.info(f"Saved conversation history for {project_id} phase {phase} (iteration {iteration}, {len(messages)} messages)")


def _write_with_backup(path: str, data: Dict[str, Any]) -> None:
    """
    Write file with backup to prevent corruption.

    Args:
        path: File path
        data: Data to write
    """
    # Create backup if file exists
    if os.path.exists(path):
        backup_path = f"{path}.backup"
        try:
            with open(path, 'r', encoding='utf-8') as f_src, open(backup_path, 'w', encoding='utf-8') as f_dst:
                f_dst.write(f_src.read())
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    # Write new data
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        # Attempt to restore from backup
        backup_path = f"{path}.backup"
        if os.path.exists(backup_path):
            with open(backup_path, 'r') as f_src, open(path, 'w') as f_dst:
                f_dst.write(f_src.read())
        raise e


def load_conversation_history(project_id: str, phase: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load conversation history from file.

    Args:
        project_id: Project ID
        phase: Current phase

    Returns:
        List of messages if found, None otherwise
    """
    history_path = get_conversation_history_path(project_id, phase)

    if not os.path.exists(history_path):
        logger.info(f"No conversation history found for {project_id} phase {phase}")
        return None

    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        messages = data.get('messages', [])
        iteration = data.get('iteration', 0)

        logger.info(f"Loaded conversation history for {project_id} phase {phase} ({len(messages)} messages, iteration {iteration})")
        return messages

    except json.JSONDecodeError as e:
        logger.error(f"Corrupted conversation history for {project_id} phase {phase}: {e}")
        # Try to load backup
        backup_path = f"{history_path}.backup"
        if os.path.exists(backup_path):
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                messages = data.get('messages', [])
                logger.warning(f"Loaded from backup ({len(messages)} messages)")
                return messages
            except Exception as backup_error:
                logger.error(f"Backup also corrupted: {backup_error}")
        return None

    except Exception as e:
        logger.error(f"Error loading conversation history: {e}")
        return None


def save_conversation_log(
    project_id: str,
    phase: str,
    messages: List[Dict[str, Any]]
) -> None:
    """
    Save human-readable conversation log (markdown format).

    This is for debugging and inspection purposes.

    Args:
        project_id: Project ID
        phase: Current phase
        messages: List of message dictionaries
    """
    log_path = get_conversation_log_path(project_id, phase)

    # Ensure directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"# Conversation Log - {project_id} - {phase}\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write("---\n\n")

        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            f.write(f"## Message {i+1}: {role.upper()}\n\n")

            if 'reasoning_content' in msg and msg['reasoning_content']:
                f.write(f"**Reasoning:**\n```\n{msg['reasoning_content']}\n```\n\n")

            if 'content' in msg and msg['content']:
                f.write(f"**Content:**\n{msg['content']}\n\n")

            if 'tool_calls' in msg and msg['tool_calls']:
                f.write(f"**Tool Calls:**\n")
                for tc in msg['tool_calls']:
                    if isinstance(tc, dict):
                        func_name = tc.get('function', {}).get('name', 'unknown')
                        func_args = tc.get('function', {}).get('arguments', '{}')
                        f.write(f"- `{func_name}`: {func_args}\n")
                f.write("\n")

            if 'name' in msg and 'tool_call_id' in msg:
                # Tool result
                f.write(f"**Tool Result ({msg['name']}):**\n```json\n{msg.get('content', '')}\n```\n\n")

            f.write("---\n\n")

    logger.debug(f"Saved conversation log to {log_path}")


def clear_conversation_history(project_id: str, phase: str) -> None:
    """
    Clear conversation history for a phase.

    Args:
        project_id: Project ID
        phase: Phase to clear
    """
    history_path = get_conversation_history_path(project_id, phase)
    if os.path.exists(history_path):
        os.remove(history_path)
        logger.info(f"Cleared conversation history for {project_id} phase {phase}")
