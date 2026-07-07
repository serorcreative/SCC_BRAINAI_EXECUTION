"""Adaptateurs LLM externes — emplacements d'extension (non branchés en V1).

Matérialisent la place d'un LLM (Claude, ChatGPT, Gemini…) pour aider au diagnostic
ou enrichir les rapports, **sans aucun appel réseau**. Indisponibles tant qu'un
transport n'est pas fourni ; le moteur les ignore alors et pilote de façon
déterministe. Un LLM ne déclenche ni ne modifie jamais une exécution.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from scc_brainai_execution.providers.base import BaseProvider


class ExternalExecutor(BaseProvider):
    name = "external"

    def __init__(self, client: Optional[Any] = None):
        self._client = client

    def available(self) -> bool:
        return self._client is not None

    def _guard(self):
        raise NotImplementedError(
            f"Fournisseur '{self.name}' : transport non implémenté dans le socle (aucun réseau).")

    def diagnose(self, run: Dict[str, Any]) -> Optional[str]:
        if not self.available():
            return None
        self._guard()

    def enrich_report(self, report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.available():
            return None
        self._guard()


class ClaudeExecutor(ExternalExecutor):
    name = "claude"


class ChatGPTExecutor(ExternalExecutor):
    name = "chatgpt"


class GeminiExecutor(ExternalExecutor):
    name = "gemini"


KNOWN_EXTERNAL = {"claude": ClaudeExecutor, "chatgpt": ChatGPTExecutor, "gemini": GeminiExecutor}

__all__ = ["ExternalExecutor", "ClaudeExecutor", "ChatGPTExecutor", "GeminiExecutor", "KNOWN_EXTERNAL"]
