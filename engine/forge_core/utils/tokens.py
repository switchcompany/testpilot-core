"""Token counting and prompt size management using tiktoken."""

from __future__ import annotations

import tiktoken


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in text for a given model."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def truncate_to_tokens(text: str, max_tokens: int, model: str = "gpt-4o") -> str:
    """Truncate text to fit within max_tokens."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")

    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens])


def fits_in_context(
    system_prompt: str,
    user_content: str,
    model: str = "gpt-4o",
    max_context: int = 128_000,
    reserve_for_response: int = 4096,
) -> bool:
    """Check if system + user content fits in the model's context window."""
    total = count_tokens(system_prompt, model) + count_tokens(user_content, model)
    return total <= (max_context - reserve_for_response)


def split_for_context(
    files: dict[str, str],
    max_tokens: int,
    model: str = "gpt-4o",
) -> list[dict[str, str]]:
    """Split a dict of {path: content} into batches that fit in context.

    Returns list of batches, each a dict of {path: content}.
    """
    batches: list[dict[str, str]] = []
    current_batch: dict[str, str] = {}
    current_tokens = 0

    for path, content in files.items():
        file_tokens = count_tokens(f"--- {path} ---\n{content}\n", model)
        if current_tokens + file_tokens > max_tokens and current_batch:
            batches.append(current_batch)
            current_batch = {}
            current_tokens = 0
        current_batch[path] = content
        current_tokens += file_tokens

    if current_batch:
        batches.append(current_batch)

    return batches
