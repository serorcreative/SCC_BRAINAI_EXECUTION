"""Fournisseurs d'exécution : déterministe (défaut) + emplacements LLM (diagnostic)."""

from __future__ import annotations

from scc_brainai_execution.providers.base import BaseProvider, ExecutionProvider
from scc_brainai_execution.providers.deterministic import DeterministicExecutor
from scc_brainai_execution.providers.external import (
    ChatGPTExecutor,
    ClaudeExecutor,
    ExternalExecutor,
    GeminiExecutor,
)
from scc_brainai_execution.providers.registry import ProviderRegistry

__all__ = [
    "ExecutionProvider", "BaseProvider", "DeterministicExecutor",
    "ExternalExecutor", "ClaudeExecutor", "ChatGPTExecutor", "GeminiExecutor",
    "ProviderRegistry",
]
