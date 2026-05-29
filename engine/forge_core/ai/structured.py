"""Structured AI outputs using instructor + pydantic."""

from __future__ import annotations

from typing import Any, TypeVar

import instructor
import litellm
from pydantic import BaseModel

from forge_core.models.config import AIConfig
from forge_core.ai.provider import _resolve_model
from forge_core.utils import logger

T = TypeVar("T", bound=BaseModel)


def extract(
    config: AIConfig,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    max_retries: int = 2,
) -> T:
    """Extract structured data from AI using instructor.

    Forces the AI to return data matching a pydantic model schema.
    Retries on validation failure.

    Args:
        config: AI provider configuration.
        system_prompt: System-level instructions.
        user_prompt: User message with code/context.
        response_model: Pydantic model class to extract.
        max_retries: Number of retries on validation failure.

    Returns:
        An instance of response_model populated by the AI.
    """
    model = _resolve_model(config)

    client = instructor.from_litellm(litellm.completion)

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": config.temperature,
        "max_retries": max_retries,
        "response_model": response_model,
    }

    if config.api_key:
        kwargs["api_key"] = config.api_key
    if config.base_url:
        kwargs["api_base"] = config.base_url

    logger.info(f"Structured extraction → {model} → {response_model.__name__}")

    try:
        result = client.chat.completions.create(**kwargs)
        logger.success(f"Extracted {response_model.__name__} successfully")
        return result
    except Exception as e:
        logger.error(f"Structured extraction failed: {e}")
        raise
