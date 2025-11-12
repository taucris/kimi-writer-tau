"""
Model provider abstraction for the Kimi Multi-Agent Novel Writing System.

This module provides a flexible architecture for supporting multiple AI model
providers (Moonshot, DeepInfra, etc.) with different API specifications.
"""

from backend.model_providers.base_provider import BaseModelProvider
from backend.model_providers.moonshot_provider import MoonshotProvider
from backend.model_providers.deepinfra_provider import DeepInfraProvider

__all__ = [
    'BaseModelProvider',
    'MoonshotProvider',
    'DeepInfraProvider',
    'get_provider',
    'list_available_models'
]


def get_provider(provider_type: str, api_key: str, **kwargs) -> BaseModelProvider:
    """
    Factory function to get a model provider instance.

    Args:
        provider_type: Type of provider ('moonshot' or 'deepinfra')
        api_key: API key for the provider
        **kwargs: Additional provider-specific configuration

    Returns:
        BaseModelProvider instance

    Raises:
        ValueError: If provider_type is not supported
    """
    providers = {
        'moonshot': MoonshotProvider,
        'deepinfra': DeepInfraProvider
    }

    provider_class = providers.get(provider_type.lower())
    if not provider_class:
        raise ValueError(
            f"Unsupported provider: {provider_type}. "
            f"Supported providers: {', '.join(providers.keys())}"
        )

    return provider_class(api_key=api_key, **kwargs)


def list_available_models():
    """
    List all available models across all providers.

    Returns:
        List of model configuration dictionaries
    """
    from backend.config import AVAILABLE_MODELS
    return AVAILABLE_MODELS
