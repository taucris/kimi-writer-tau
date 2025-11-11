"""
Robust file writing utilities with atomic operations and safety checks.

Provides utilities for safely writing files with backup and validation.
"""

import os
import tempfile
import shutil
from typing import Optional


def atomic_write(
    file_path: str,
    content: str,
    encoding: str = 'utf-8',
    backup: bool = True
) -> None:
    """
    Atomically write content to a file with optional backup.

    This prevents file corruption if the process crashes mid-write.

    Args:
        file_path: Target file path
        content: Content to write
        encoding: File encoding (default utf-8)
        backup: Whether to create a backup of existing file

    Raises:
        IOError: If write fails
        ValueError: If content is empty
    """
    # Validate content
    if not content or not content.strip():
        raise ValueError("Cannot write empty content to file")

    # Check disk space (basic check - 10MB minimum)
    # Skip on Windows as statvfs doesn't exist
    if hasattr(os, 'statvfs'):
        try:
            stat = os.statvfs(os.path.dirname(file_path) or '.')
            available_space = stat.f_bavail * stat.f_frsize
            if available_space < 10 * 1024 * 1024:  # 10 MB
                raise IOError(f"Insufficient disk space: {available_space / 1024 / 1024:.1f} MB available")
        except Exception:
            # If disk space check fails, continue anyway
            pass

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Create backup if file exists and backup is requested
    if backup and os.path.exists(file_path):
        backup_path = f"{file_path}.backup"
        try:
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            # Log warning but don't fail - backup is best-effort
            import logging
            logging.getLogger(__name__).warning(f"Failed to create backup: {e}")

    # Write to temporary file first (atomic operation)
    dir_name = os.path.dirname(file_path)
    fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix='.tmp_', suffix='.md')

    try:
        # Write content to temp file
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk

        # Atomic rename (replaces target file)
        # On Windows, need to remove target first if it exists
        if os.name == 'nt' and os.path.exists(file_path):
            os.replace(temp_path, file_path)
        else:
            os.rename(temp_path, file_path)

    except Exception as e:
        # Clean up temp file on error
        try:
            os.remove(temp_path)
        except:
            pass
        raise IOError(f"Failed to write file {file_path}: {e}") from e


def safe_read(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read a file with error handling.

    Args:
        file_path: File to read
        encoding: File encoding

    Returns:
        File content or None if file doesn't exist/can't be read
    """
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to read {file_path}: {e}")
        return None


def validate_content(content: str, min_words: int = 0, min_chars: int = 0) -> tuple[bool, str]:
    """
    Validate content before writing.

    Args:
        content: Content to validate
        min_words: Minimum word count (0 = no limit)
        min_chars: Minimum character count (0 = no limit)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content:
        return False, "Content is empty"

    if not content.strip():
        return False, "Content contains only whitespace"

    if min_words > 0:
        word_count = len(content.split())
        if word_count < min_words:
            return False, f"Content has {word_count} words, minimum is {min_words}"

    if min_chars > 0:
        if len(content) < min_chars:
            return False, f"Content has {len(content)} characters, minimum is {min_chars}"

    return True, ""
