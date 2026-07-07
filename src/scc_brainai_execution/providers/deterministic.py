"""Exécuteur déterministe — le pilotage/suivi/rapport par défaut de BrainAI Execution.

Aucun LLM, aucun réseau : le pilotage est porté par des règles pures. Ce fournisseur
garantit que Execution **fonctionne toujours**, même sans IA.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from scc_brainai_execution.providers.base import BaseProvider


class DeterministicExecutor(BaseProvider):
    name = "deterministic"

    def available(self) -> bool:
        return True

    def diagnose(self, run: Dict[str, Any]) -> Optional[str]:
        return None

    def enrich_report(self, report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None


__all__ = ["DeterministicExecutor"]
