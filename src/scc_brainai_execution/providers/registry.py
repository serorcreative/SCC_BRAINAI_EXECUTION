"""Registre des fournisseurs d'exécution — repli déterministe garanti."""

from __future__ import annotations

from typing import Dict, List, Optional

from scc_brainai_execution.providers.base import BaseProvider
from scc_brainai_execution.providers.deterministic import DeterministicExecutor
from scc_brainai_execution.providers.external import KNOWN_EXTERNAL


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, BaseProvider] = {}
        self.register(DeterministicExecutor())
        for name, cls in KNOWN_EXTERNAL.items():
            self.register(cls())

    def register(self, provider: BaseProvider) -> BaseProvider:
        self._providers[provider.name] = provider
        return provider

    def names(self) -> List[str]:
        return sorted(self._providers)

    def available(self) -> List[str]:
        return sorted(n for n, p in self._providers.items() if p.available())

    def select(self, order: Optional[List[str]] = None) -> BaseProvider:
        for name in (order or []):
            p = self._providers.get(name)
            if p is not None and p.available():
                return p
        return self._providers["deterministic"]

    def to_dict(self) -> Dict[str, object]:
        return {"registered": self.names(), "available": self.available(),
                "external_slots": sorted(KNOWN_EXTERNAL)}


__all__ = ["ProviderRegistry"]
