"""Contrat des fournisseurs d'exécution — point d'extension pour un futur LLM.

L'exécution **ne dépend d'aucun LLM** : le pilotage, le suivi et le rapport par
défaut sont déterministes. Un LLM pourra plus tard *aider à diagnostiquer* un échec
ou *enrichir* un rapport d'exécution — **sans jamais** en devenir un prérequis, ni
déclencher, ni modifier une exécution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ExecutionProvider(Protocol):
    name: str

    def available(self) -> bool: ...

    def diagnose(self, run: Dict[str, Any]) -> Optional[str]: ...

    def enrich_report(self, report: Dict[str, Any]) -> Optional[Dict[str, Any]]: ...


class BaseProvider:
    name = "base"

    def available(self) -> bool:
        return False

    def diagnose(self, run: Dict[str, Any]) -> Optional[str]:
        return None

    def enrich_report(self, report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None


__all__ = ["ExecutionProvider", "BaseProvider"]
