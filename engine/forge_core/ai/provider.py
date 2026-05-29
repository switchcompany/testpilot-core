"""LiteLLM-based AI provider — unified interface for 100+ models."""

from __future__ import annotations

from typing import Any

import litellm

from forge_core.models.config import AIConfig, AIProvider
from forge_core.utils import logger
from forge_core.utils.tokens import count_tokens

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True


def _resolve_model(config: AIConfig) -> str:
    """Resolve the model string for LiteLLM based on provider."""
    if config.provider == AIProvider.OLLAMA:
        return f"ollama/{config.model}"
    if config.provider == AIProvider.AZURE:
        return f"azure/{config.model}"
    if config.provider == AIProvider.BEDROCK:
        return f"bedrock/{config.model}"
    return config.model


def complete(
    config: AIConfig,
    system_prompt: str,
    user_prompt: str,
    json_mode: bool = False,
    max_tokens: int | None = None,
) -> str:
    """Send a completion request to the configured AI provider.

    Args:
        config: AI provider configuration.
        system_prompt: System-level instructions.
        user_prompt: User message with code/context.
        json_mode: If True, request JSON response format.
        max_tokens: Override max tokens for this call.

    Returns:
        The AI's response text.
    """
    model = _resolve_model(config)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": max_tokens or config.max_tokens,
    }

    if config.api_key:
        kwargs["api_key"] = config.api_key
    if config.base_url:
        kwargs["api_base"] = config.base_url
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    # Log token usage
    input_tokens = count_tokens(system_prompt + user_prompt, config.model)
    logger.info(f"AI call → {model} ({input_tokens} input tokens)")

    try:
        response = litellm.completion(**kwargs)
        content = response.choices[0].message.content or ""

        output_tokens = count_tokens(content, config.model)
        logger.info(f"AI response ← {output_tokens} output tokens")

        return content
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        raise


def complete_with_fallback(
    config: AIConfig,
    system_prompt: str,
    user_prompt: str,
    fallback_models: list[str] | None = None,
    json_mode: bool = False,
) -> str:
    """Try primary model, fall back to alternatives on failure.

    Useful for complex classes where one model might fail.
    """
    models = [_resolve_model(config)] + (fallback_models or [])

    last_error = None
    for model in models:
        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            }
            if config.api_key:
                kwargs["api_key"] = config.api_key
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = litellm.completion(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            last_error = e
            logger.warn(f"Model {model} failed, trying next: {e}")
            continue

    raise RuntimeError(f"All models failed. Last error: {last_error}")
