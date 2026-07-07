"""Pont Runtime — l'exécution **délègue** au Runtime via ses interfaces publiques.

Execution ne réalise **aucune action technique** elle-même : elle instancie un
``RuntimeEngine`` (horloge et fabrique d'identifiants **injectées** pour le
déterminisme), soumet un job par étape, respecte la gouvernance du Runtime (une
action T3 est bloquée puis validée humainement), et collecte résultats + événements.
Le Runtime n'est **pas modifié**.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any, Dict, List, Optional, Tuple

from scc_brainai_execution.core.config import ExecutionConfig
from scc_brainai_execution.core.errors import SourceUnavailable


class RuntimeBridge:
    def __init__(self, config: ExecutionConfig):
        self._config = config
        self._rt = None

    def _ensure(self):
        if self._rt is not None:
            return self._rt
        src = self._config.runtime_src
        if not src.exists():
            raise SourceUnavailable(f"Runtime SCC introuvable : {src}")
        if str(src) not in sys.path:
            sys.path.insert(0, str(src))
        try:
            self._rt = importlib.import_module("scc_runtime")
        except ImportError as exc:  # pragma: no cover
            raise SourceUnavailable(f"Import du Runtime impossible : {exc}") from exc
        return self._rt

    @property
    def available(self) -> bool:
        try:
            self._ensure()
            return True
        except SourceUnavailable:
            return False

    def delegate(self, steps: List[Any], actor: str, autonomy: str,
                 approver: str) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
        """Exécute chaque étape comme un job Runtime (déterministe). Renvoie
        (résultats par étape, événements Runtime)."""
        rt = self._ensure()
        from scc_runtime.core.clock import FixedClock, SequentialFactory

        engine = rt.RuntimeEngine(clock=FixedClock(self._config.as_of), id_factory=SequentialFactory())
        events: List[Dict[str, Any]] = []
        engine.events.subscribe(lambda e: events.append(e.to_dict()))
        engine.boot()
        session = engine.open_session(actor=actor, autonomy=rt.AutonomyLevel(autonomy),
                                      label="BrainAI execution")
        results: Dict[str, Dict[str, Any]] = {}
        for step in steps:
            job = engine.submit(session.id, step.kind, dict(step.params))
            approved = False
            if job.status.value == "blocked":       # garde-fou T3 du Runtime
                engine.approve(job.id, approver=approver)
                approved = True
            engine.run_all()
            results[step.id] = {"job_id": job.id, "status": job.status.value,
                                "result": job.result, "error": job.error,
                                "human_approval_required": approved,
                                "trust": job.trust.value}
        engine.shutdown()
        return results, events


__all__ = ["RuntimeBridge"]
