"""The model configurations CP-OS and the run start page select (``--config``).

Moved from ``model_testing/configs.py`` when the model-testing harness was retired (owner,
2026-11-15); the definitions are unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from deploy_workflow.model.turn import Provider

Role = Literal["repair", "comparison"]


@dataclass(frozen=True)
class ModelConfig:
    config_id: str
    provider: Provider
    model: str
    effort: str
    roles: frozenset[Role]


CONFIGS: Mapping[str, ModelConfig] = MappingProxyType(
    {
        "sol-medium": ModelConfig(
            "sol-medium", "openai", "gpt-6.1-sol", "medium", frozenset({"repair", "comparison"})
        ),
        "sol-high": ModelConfig(
            "sol-high", "openai", "gpt-6.1-sol", "high", frozenset({"comparison"})
        ),
        "opus-medium": ModelConfig(
            "opus-medium", "anthropic", "claude-opus-5-5", "medium", frozenset({"comparison"})
        ),
        # no model-testing stage plans it; selected by CP-OS / the run start page (owner 2026-11-12)
        "opus-high": ModelConfig("opus-high", "anthropic", "claude-opus-5-5", "high", frozenset()),
        "deepseek-max": ModelConfig(
            "deepseek-max",
            "openrouter",
            "deepseek/deepseek-v4.1-flash-1017",
            "max",
            frozenset(),  # defined for its recorded spend; no stage plans it (user, 2026-11-02)
        ),
        # no model-testing stage plans a Copilot run; selected explicitly by CP-OS (plan 2026-11-06)
        "copilot-sol-medium": ModelConfig(
            "copilot-sol-medium", "copilot", "gpt-6.1-sol", "medium", frozenset()
        ),
        "copilot-opus-medium": ModelConfig(
            "copilot-opus-medium", "copilot", "claude-opus-5.5", "medium", frozenset()
        ),
    }
)
