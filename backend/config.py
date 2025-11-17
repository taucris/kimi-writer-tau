"""
Configuration management for the Kimi Multi-Agent Novel Writing System.

This module provides Pydantic models for all configuration needs:
- NovelConfig: Main configuration for novel generation
- AgentConfig: Agent-specific settings (prompts, iterations)
- WritingSampleConfig: Writing sample selection
- CheckpointConfig: Approval checkpoint settings
- APIConfig: Moonshot AI API credentials and settings
"""

import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class NovelLength(str, Enum):
    """Enum for novel length options."""
    SHORT_STORY = "short_story"  # 3,000-10,000 words
    NOVELLA = "novella"  # 20,000-50,000 words
    NOVEL = "novel"  # 50,000-110,000 words
    VERY_LONG_NOVEL = "very_long_novel"  # 110,000-200,000 words
    CUSTOM = "custom"  # Custom word count specified by user


class Phase(str, Enum):
    """Enum for workflow phases."""
    PLANNING = "PLANNING"
    PLAN_CRITIQUE = "PLAN_CRITIQUE"
    WRITING = "WRITING"
    WRITE_CRITIQUE = "WRITE_CRITIQUE"
    COMPLETE = "COMPLETE"


class WritingSampleConfig(BaseModel):
    """Configuration for writing sample selection."""
    sample_id: Optional[str] = None  # Preset sample ID or 'custom'
    custom_text: Optional[str] = None  # Custom sample text if sample_id is 'custom'
    enabled: bool = False  # Whether to use writing sample

    @field_validator('custom_text')
    @classmethod
    def validate_custom_text(cls, v, info):
        """Validate custom text length."""
        if v and len(v) < 100:
            raise ValueError("Custom writing sample must be at least 100 characters")
        return v


class CheckpointConfig(BaseModel):
    """Configuration for approval checkpoints."""
    require_plan_approval: bool = True  # Approval after planning phase
    require_plan_critique_approval: bool = False  # Approval after each plan critique
    require_chunk_approval: bool = False  # Approval after each chunk
    require_chunk_critique_approval: bool = False  # Approval after each critique


class AgentConfig(BaseModel):
    """Configuration for agent behavior."""
    max_plan_critique_iterations: int = Field(default=2, ge=1, le=10)
    max_write_critique_iterations: int = Field(default=2, ge=1, le=10)

    # System prompt overrides (None = use defaults)
    planning_prompt_override: Optional[str] = None
    plan_critic_prompt_override: Optional[str] = None
    writing_prompt_override: Optional[str] = None
    write_critic_prompt_override: Optional[str] = None


class ModelConfig(BaseModel):
    """Configuration for a specific AI model."""
    id: str  # Unique identifier (e.g., 'kimi-k2-thinking', 'zai-org/GLM-4.6')
    name: str  # Display name
    provider: str  # Provider type ('moonshot', 'deepinfra')
    context_window: int  # Maximum context window in tokens
    supports_reasoning: bool = False  # Whether model outputs reasoning traces
    supports_tools: bool = True  # Whether model supports function calling
    description: str = ""  # Description for UI
    pricing: Optional[str] = None  # Pricing info (e.g., "$0.45/M in, $1.90/M out")


# Available models configuration
AVAILABLE_MODELS = [
    {
        "id": "kimi-k2-thinking",
        "name": "Kimi K2 Thinking",
        "provider": "moonshot",
        "context_window": 200000,
        "supports_reasoning": True,
        "supports_tools": True,
        "description": "Moonshot AI's most advanced model with reasoning capabilities. Best quality but slower.",
        "pricing": "Variable"
    },
    {
        "id": "zai-org/GLM-4.6",
        "name": "GLM-4.6",
        "provider": "deepinfra",
        "context_window": 200000,
        "supports_reasoning": False,
        "supports_tools": True,
        "description": "Fast and capable model with 200K context window. Great for testing and faster iterations.",
        "pricing": "$0.45/M in, $1.90/M out"
    }
]


class APIConfig(BaseModel):
    """Configuration for AI API."""
    # API keys for different providers
    moonshot_api_key: Optional[str] = None
    deepinfra_api_key: Optional[str] = None

    # Selected model
    model_id: str = "kimi-k2-thinking"  # Default to Kimi

    # Legacy field for backward compatibility
    api_key: Optional[str] = None  # Will be mapped to moonshot_api_key if present
    base_url: Optional[str] = None  # Legacy, now determined by provider
    model_name: Optional[str] = None  # Legacy, now model_id

    # Model-independent settings
    token_limit: int = 200000
    compression_threshold: int = 180000  # Start compression at 90% of limit
    max_iterations: int = 300  # Safety limit for infinite loops

    def get_provider_api_key(self, provider: str) -> str:
        """
        Get API key for a specific provider.

        Args:
            provider: Provider name ('moonshot' or 'deepinfra')

        Returns:
            API key string

        Raises:
            ValueError: If API key not found for provider
        """
        # Handle legacy api_key field
        if provider == 'moonshot':
            key = self.moonshot_api_key or self.api_key
            if not key:
                raise ValueError("Moonshot API key not configured")
            return key
        elif provider == 'deepinfra':
            if not self.deepinfra_api_key:
                raise ValueError("DeepInfra API key not configured")
            return self.deepinfra_api_key
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def get_model_config(self) -> Optional[Dict[str, Any]]:
        """
        Get configuration for the selected model.

        Returns:
            Model configuration dictionary or None if not found
        """
        # Handle legacy model_name field
        model_id = self.model_id or self.model_name or "kimi-k2-thinking"

        for model in AVAILABLE_MODELS:
            if model["id"] == model_id:
                return model
        return None


class NovelConfig(BaseModel):
    """Main configuration for novel generation."""
    # Project identification
    project_id: str
    project_name: str

    # Novel parameters
    novel_length: NovelLength = NovelLength.NOVEL
    custom_word_count: Optional[int] = None  # Custom word count when novel_length is CUSTOM
    theme: str = ""  # User's initial prompt/theme
    genre: Optional[str] = None

    # Sub-configurations
    writing_sample: WritingSampleConfig = Field(default_factory=WritingSampleConfig)
    checkpoints: CheckpointConfig = Field(default_factory=CheckpointConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    api: APIConfig

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


def generate_project_id(project_name: str) -> str:
    """
    Generate a unique project ID based on project name and timestamp.

    Format: "{project_name} - {timestamp}"
    Example: "For whom the bell tolls - 20251116_225433"

    Args:
        project_name: User-provided project name (will be sanitized)

    Returns:
        Project ID string
    """
    sanitized_name = sanitize_project_name(project_name)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{sanitized_name} - {timestamp}"


def sanitize_project_name(name: str) -> str:
    """
    Sanitize project name for filesystem compatibility.

    Preserves spaces and common punctuation for readability while ensuring
    filesystem safety.

    Args:
        name: Raw project name

    Returns:
        Sanitized project name
    """
    # Replace characters that are problematic for filesystems
    # Allow: letters, numbers, spaces, hyphens, apostrophes, commas
    sanitized = "".join(c if c.isalnum() or c in (' ', '-', "'", ',') else '' for c in name)
    # Collapse multiple spaces into single space
    sanitized = ' '.join(sanitized.split())
    # Limit length (reserve space for timestamp: " - 20251116_225433" = 20 chars)
    max_name_length = 80  # Allow longer names since we're using readable format
    sanitized = sanitized[:max_name_length].strip()
    return sanitized


def load_config_from_file(path: str) -> NovelConfig:
    """
    Load configuration from a JSON file.

    Args:
        path: Path to config file

    Returns:
        NovelConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return NovelConfig(**data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading config: {e}")


def save_config_to_file(config: NovelConfig, path: str) -> None:
    """
    Save configuration to a JSON file.

    Args:
        config: NovelConfig instance
        path: Path to save config file
    """
    # Update timestamp
    config.updated_at = datetime.now()

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Write config
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(
            config.model_dump(mode='json'),
            f,
            indent=2,
            ensure_ascii=False
        )


def validate_config(config: NovelConfig) -> bool:
    """
    Validate configuration.

    Args:
        config: NovelConfig instance

    Returns:
        True if valid

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate API key for selected model
    model_config = config.api.get_model_config()
    if not model_config:
        raise ValueError(f"Unknown model: {config.api.model_id}")

    provider = model_config['provider']
    try:
        config.api.get_provider_api_key(provider)
    except ValueError as e:
        raise ValueError(f"API key validation failed: {e}")

    # Validate project name
    if not config.project_name:
        raise ValueError("Project name is required")

    # Validate writing sample
    if config.writing_sample.enabled:
        if not config.writing_sample.sample_id:
            raise ValueError("Writing sample ID required when enabled")
        if config.writing_sample.sample_id == 'custom' and not config.writing_sample.custom_text:
            raise ValueError("Custom text required when sample_id is 'custom'")

    return True


def get_default_config(
    project_name: str,
    theme: str,
    api_key: Optional[str] = None,
    moonshot_api_key: Optional[str] = None,
    deepinfra_api_key: Optional[str] = None,
    model_id: str = "kimi-k2-thinking"
) -> NovelConfig:
    """
    Get default configuration with minimal user input.

    Args:
        project_name: Name for the project
        theme: User's theme/prompt
        api_key: Legacy Moonshot API key (for backward compatibility)
        moonshot_api_key: Moonshot API key
        deepinfra_api_key: DeepInfra API key
        model_id: Model identifier (default: kimi-k2-thinking)

    Returns:
        NovelConfig with default settings
    """
    project_id = generate_project_id(project_name)
    sanitized_name = sanitize_project_name(project_name)

    # Handle legacy api_key parameter
    if api_key and not moonshot_api_key:
        moonshot_api_key = api_key

    return NovelConfig(
        project_id=project_id,
        project_name=sanitized_name,
        theme=theme,
        api=APIConfig(
            api_key=api_key,  # Keep for legacy compatibility
            moonshot_api_key=moonshot_api_key,
            deepinfra_api_key=deepinfra_api_key,
            model_id=model_id
        )
    )


def get_config_path(project_id: str) -> str:
    """
    Get path to config file for a project.

    Args:
        project_id: Project ID

    Returns:
        Path to config file
    """
    return f"output/{project_id}/.novel_config.json"


def load_or_create_config(
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    theme: Optional[str] = None,
    api_key: Optional[str] = None
) -> NovelConfig:
    """
    Load existing config or create new one.

    Args:
        project_id: Existing project ID (if loading)
        project_name: New project name (if creating)
        theme: Theme/prompt (if creating)
        api_key: API key (if creating)

    Returns:
        NovelConfig instance
    """
    if project_id:
        # Load existing
        config_path = get_config_path(project_id)
        return load_config_from_file(config_path)
    else:
        # Create new
        if not all([project_name, theme, api_key]):
            raise ValueError("project_name, theme, and api_key required for new project")
        return get_default_config(project_name, theme, api_key)
