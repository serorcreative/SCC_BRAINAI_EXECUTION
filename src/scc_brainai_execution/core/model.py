"""Modèle d'exécution BrainAI.

Une **ExecutionRun** matérialise le pilotage contrôlé d'un **manifeste décisionnel
validé** : garde-fous, étapes (**ExecutionStep**) déléguées au Runtime, suivi d'état,
journal d'événements, rapport, et **traces exploitables par Memory plus tard**.

Tout est déterministe (identifiants dérivés du contenu) et **gouverné** : rien ne
s'exécute sans manifeste validé ni sans autorisation explicite. Aucune couche n'est
modifiée (le manifeste de la décision est lu, jamais muté).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Dict, List

from scc_brainai_execution.core.clock import digest, short_id


class RunStatus(str, Enum):
    PREPARED = "prepared"       # garde-fous OK, étapes prêtes ; pas encore exécuté
    REFUSED = "refused"         # garde-fous KO : exécution interdite
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVOKED = "revoked"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


_RUN_TRANSITIONS = {
    "prepared": {"running", "cancelled", "revoked"},
    "running": {"succeeded", "failed", "cancelled", "revoked"},
    "succeeded": {"revoked"},
    "failed": set(),
    "cancelled": set(),
    "revoked": set(),
    "refused": set(),
}


def can_transition(current: str, target: str) -> bool:
    return target in _RUN_TRANSITIONS.get(current, set())


@dataclass
class ExecutionStep:
    """Étape d'exécution, déléguée au Runtime via un job."""

    order: int = 0
    name: str = ""
    kind: str = "echo"                       # type de job Runtime
    params: Dict[str, Any] = field(default_factory=dict)
    status: str = StepStatus.PENDING.value
    result: Dict[str, Any] = field(default_factory=dict)
    job_id: str = ""
    sources: List[str] = field(default_factory=list)
    id: str = ""
    hash: str = ""

    KIND: ClassVar[str] = "step"

    def _content(self) -> Dict[str, Any]:
        return {"order": self.order, "name": self.name, "kind": self.kind,
                "params": self.params, "sources": sorted(self.sources)}

    def finalize(self) -> "ExecutionStep":
        self.id = short_id("step", self._content())
        self.hash = digest(self._content())
        return self

    def verify(self) -> bool:
        return self.hash == digest(self._content())

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "order": self.order, "name": self.name, "kind": self.kind,
                "params": dict(self.params), "status": self.status, "result": dict(self.result),
                "job_id": self.job_id, "sources": list(self.sources), "hash": self.hash}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExecutionStep":
        s = cls(order=int(d.get("order", 0)), name=str(d.get("name", "")),
                kind=str(d.get("kind", "echo")), params=dict(d.get("params", {}) or {}),
                status=str(d.get("status", "pending")), result=dict(d.get("result", {}) or {}),
                job_id=str(d.get("job_id", "")), sources=list(d.get("sources", []) or []))
        s.id = str(d.get("id", "")) or s.finalize().id
        s.hash = str(d.get("hash", "")) or s.hash
        return s


@dataclass
class ExecutionRequest:
    """Demande d'exécution : référence de décision et/ou manifeste + statut."""

    decision_id: str = ""
    manifest: Dict[str, Any] = field(default_factory=dict)
    decision_status: str = ""              # statut de la décision (doit être 'validated')
    actor: str = "brainai"                 # acteur déclencheur (doit être autorisé)
    tags: List[str] = field(default_factory=list)
    id: str = ""

    def finalize(self) -> "ExecutionRequest":
        self.id = short_id("exreq", {"decision_id": self.decision_id,
                                     "manifest": self.manifest})
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "decision_id": self.decision_id, "manifest": dict(self.manifest),
                "decision_status": self.decision_status, "actor": self.actor,
                "tags": list(self.tags)}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExecutionRequest":
        r = cls(decision_id=str(d.get("decision_id", "")), manifest=dict(d.get("manifest", {}) or {}),
                decision_status=str(d.get("decision_status", "")),
                actor=str(d.get("actor", "brainai")), tags=list(d.get("tags", []) or []))
        r.id = str(d.get("id", "")) or r.finalize().id
        return r


@dataclass
class ExecutionRun:
    """Pilotage contrôlé d'une exécution."""

    request: ExecutionRequest
    as_of: str = ""
    decision_id: str = ""
    subject: str = ""
    guards: Dict[str, Any] = field(default_factory=dict)
    steps: List[ExecutionStep] = field(default_factory=list)
    status: str = RunStatus.PREPARED.value
    events: List[Dict[str, Any]] = field(default_factory=list)
    report: Dict[str, Any] = field(default_factory=dict)
    traces_for_memory: List[Dict[str, Any]] = field(default_factory=list)
    authorization: Dict[str, Any] = field(default_factory=dict)
    provider: str = "deterministic"
    id: str = ""

    def finalize(self) -> "ExecutionRun":
        self.id = short_id("exec", {"request": self.request.id,
                                    "steps": [s.id for s in self.steps]})
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "as_of": self.as_of, "provider": self.provider,
                "decision_id": self.decision_id, "subject": self.subject,
                "request": self.request.to_dict(), "guards": dict(self.guards),
                "steps": [s.to_dict() for s in self.steps], "status": self.status,
                "events": list(self.events), "report": dict(self.report),
                "traces_for_memory": list(self.traces_for_memory),
                "authorization": dict(self.authorization)}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExecutionRun":
        run = cls(request=ExecutionRequest.from_dict(d.get("request", {})),
                  as_of=str(d.get("as_of", "")), decision_id=str(d.get("decision_id", "")),
                  subject=str(d.get("subject", "")), guards=dict(d.get("guards", {}) or {}),
                  steps=[ExecutionStep.from_dict(x) for x in d.get("steps", [])],
                  status=str(d.get("status", "prepared")), events=list(d.get("events", []) or []),
                  report=dict(d.get("report", {}) or {}),
                  traces_for_memory=list(d.get("traces_for_memory", []) or []),
                  authorization=dict(d.get("authorization", {}) or {}),
                  provider=str(d.get("provider", "deterministic")))
        run.id = str(d.get("id", "")) or run.finalize().id
        return run


__all__ = ["RunStatus", "StepStatus", "can_transition",
           "ExecutionStep", "ExecutionRequest", "ExecutionRun"]
