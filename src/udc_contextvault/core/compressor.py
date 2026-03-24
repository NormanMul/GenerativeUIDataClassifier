"""UDC ContextVault — Context compressor for token-budget management.

Compresses a set of retrieved context entries to fit within a target
token limit by ranking, truncating, and layer-downgrading lower-ranked
entries.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token."""
    return max(1, len(text) // 4)


class ConversationCompressor:
    """Compress retrieved context to fit within a token budget.

    Uses a strategy of sorting by relevance and iteratively truncating
    or removing the lowest-ranked entries until the total fits within
    the limit.
    """

    def __init__(self, max_tokens: int = 4096) -> None:
        self.max_tokens = max_tokens

    def compress(self, entries: list[dict[str, Any]], max_tokens: int | None = None) -> list[dict[str, Any]]:
        """Compress context entries to fit within a token limit.

        Args:
            entries: List of context entry dicts, each containing at
                minimum ``content`` (str) and ``score`` (float).
            max_tokens: Override the default token budget.

        Returns:
            A subset of entries (potentially with truncated content)
            that fits within the token budget, ordered by relevance.
        """
        budget = max_tokens or self.max_tokens
        if not entries:
            return []

        # Sort by relevance score descending.
        ranked = sorted(entries, key=lambda e: e.get("score", 0.0), reverse=True)

        result: list[dict[str, Any]] = []
        tokens_used = 0

        for entry in ranked:
            content = entry.get("content", "")
            entry_tokens = estimate_tokens(content)

            if tokens_used + entry_tokens <= budget:
                result.append(entry)
                tokens_used += entry_tokens
            else:
                # Try to fit a truncated version of this entry.
                remaining = budget - tokens_used
                if remaining > 20:  # Only include if we can fit meaningful content.
                    char_limit = remaining * 4
                    truncated = content[:char_limit].rsplit(" ", 1)[0] + "…"
                    result.append({**entry, "content": truncated, "truncated": True})
                    tokens_used += estimate_tokens(truncated)
                # No more budget — stop.
                break

        logger.info(
            "compressor.compress",
            input_count=len(entries),
            output_count=len(result),
            tokens_used=tokens_used,
            budget=budget,
        )
        return result

    def extract_memories(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Distil key facts from a conversation message sequence.

        Extracts salient facts, user preferences, decisions, and
        outstanding action items by analysing conversation turns.

        Args:
            messages: Ordered list of message dicts with ``role`` and
                ``content`` keys.

        Returns:
            List of memory dicts with ``fact``, ``category``,
            ``confidence``, and ``source_turns`` keys.
        """
        memories: list[dict[str, Any]] = []

        for idx, msg in enumerate(messages):
            content = msg.get("content", "")
            role = msg.get("role", "")

            # Heuristic extraction of decisions and action items.
            sentences = [s.strip() for s in content.replace("!", ".").replace("?", ".").split(".") if s.strip()]

            for sentence in sentences:
                lower = sentence.lower()

                if any(kw in lower for kw in ("decide", "decision", "agreed", "confirmed", "will go with")):
                    memories.append(
                        {
                            "fact": sentence,
                            "category": "decision",
                            "confidence": 0.8,
                            "source_turns": [idx],
                        }
                    )
                elif any(kw in lower for kw in ("todo", "action item", "need to", "must", "should")):
                    memories.append(
                        {
                            "fact": sentence,
                            "category": "action_item",
                            "confidence": 0.7,
                            "source_turns": [idx],
                        }
                    )
                elif any(kw in lower for kw in ("prefer", "like", "always", "never", "want")):
                    memories.append(
                        {
                            "fact": sentence,
                            "category": "preference",
                            "confidence": 0.75,
                            "source_turns": [idx],
                        }
                    )

            # Always store a context-level summary for user messages.
            if role == "user" and len(content) > 100:
                memories.append(
                    {
                        "fact": content[:200],
                        "category": "context",
                        "confidence": 0.6,
                        "source_turns": [idx],
                    }
                )

        return memories
