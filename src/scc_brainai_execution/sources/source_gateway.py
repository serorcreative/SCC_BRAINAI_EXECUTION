"""Passerelle de sources — récupère décision (15) et plan (14) via interfaces publiques.

Réutilise, **sans les modifier**, ``DecisionEngine.get`` et ``PlanningEngine.get``
pour, respectivement, valider le manifeste et matérialiser les étapes. Localisation
dynamique ; **optionnelle et dégradable**.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any, Dict, Optional

from scc_brainai_execution.core.config import ExecutionConfig


class SourceGateway:
    def __init__(self, config: ExecutionConfig, decision_engine: Optional[Any] = None,
                 planning_engine: Optional[Any] = None):
        self._config = config
        self._decision = decision_engine
        self._planning = planning_engine
        self._tried = {"decision": decision_engine is not None, "planning": planning_engine is not None}

    def _add_path(self, path) -> bool:
        if not path.exists():
            return False
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
        return True

    def _decision_engine(self):
        if self._decision is None and not self._tried["decision"]:
            self._tried["decision"] = True
            if self._add_path(self._config.decision_src):
                try:
                    self._decision = importlib.import_module("scc_brainai_decision").DecisionEngine()
                except Exception:  # noqa: BLE001
                    self._decision = None
        return self._decision

    def _planning_engine(self):
        if self._planning is None and not self._tried["planning"]:
            self._tried["planning"] = True
            if self._add_path(self._config.planning_src):
                try:
                    self._planning = importlib.import_module("scc_brainai_planning").PlanningEngine()
                except Exception:  # noqa: BLE001
                    self._planning = None
        return self._planning

    def available(self) -> Dict[str, bool]:
        return {"decision": self._decision_engine() is not None,
                "planning": self._planning_engine() is not None}

    def decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        eng = self._decision_engine()
        if eng is None or not decision_id:
            return None
        try:
            return eng.get(decision_id)
        except Exception:  # noqa: BLE001
            return None

    def planset(self, ps_id: str) -> Optional[Dict[str, Any]]:
        eng = self._planning_engine()
        if eng is None or not ps_id:
            return None
        try:
            return eng.get(ps_id)
        except Exception:  # noqa: BLE001
            return None


__all__ = ["SourceGateway"]
