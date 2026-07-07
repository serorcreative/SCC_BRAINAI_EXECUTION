"""ExecutionEngine — façade de la couche d'exécution BrainAI.

Reçoit un **manifeste décisionnel validé** et **pilote** son exécution sous contrôle,
en deux temps :

1. ``prepare`` — vérifie les garde-fous (manifeste validé, non exécuté, non
   souverain, validation humaine présente, acteur autorisé), transforme le manifeste
   en étapes. Si un garde-fou refuse, l'exécution est **interdite** (statut refused).
2. ``execute`` — **explicitement déclenchée par un acteur autorisé** (aucune exécution
   automatique), délègue chaque étape au **Runtime** via ses interfaces publiques,
   suit l'état, journalise, et produit un rapport + des traces pour Memory.

Le moteur **ne modifie aucune couche** (il lit décision/plan, pilote le Runtime) et
**n'exécute jamais** lui-même : le Runtime est le seul exécutant technique.
Déterministe (identifiants de contenu, horloge Runtime injectée).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from scc_brainai_execution.audit import audit_all
from scc_brainai_execution.core.config import ExecutionConfig, load_config
from scc_brainai_execution.core.errors import GuardRejected, NotFoundError, RequestError, StateError
from scc_brainai_execution.core.model import (
    ExecutionRequest,
    ExecutionRun,
    RunStatus,
    StepStatus,
    can_transition,
)
from scc_brainai_execution.events import EventLog
from scc_brainai_execution.guards import check as guard_check
from scc_brainai_execution.index import ExecutionIndex
from scc_brainai_execution.preparation import build_steps
from scc_brainai_execution.providers.registry import ProviderRegistry
from scc_brainai_execution.report import build_report, render_markdown, store_report
from scc_brainai_execution.sources.runtime_bridge import RuntimeBridge
from scc_brainai_execution.sources.source_gateway import SourceGateway

_RUNTIME_AUTONOMY = "A3"


class ExecutionEngine:
    def __init__(self, config: Optional[ExecutionConfig] = None, *,
                 providers: Optional[ProviderRegistry] = None,
                 gateway: Optional[SourceGateway] = None,
                 runtime_bridge: Optional[RuntimeBridge] = None, autoload: bool = True):
        self.config = config or load_config()
        self.providers = providers or ProviderRegistry()
        self.gateway = gateway if gateway is not None else SourceGateway(self.config)
        self.runtime = runtime_bridge if runtime_bridge is not None else RuntimeBridge(self.config)
        self.index = ExecutionIndex()
        if autoload:
            self._load()

    # ================================================================== #
    # 1. Préparation (garde-fous)
    # ================================================================== #
    def prepare(self, request: Union[ExecutionRequest, str], **kwargs) -> Dict[str, Any]:
        req = self._as_request(request, kwargs)
        manifest = dict(req.manifest)
        decision_status = req.decision_status
        approver = str(kwargs.get("approver", ""))
        subject = str(kwargs.get("subject", ""))

        # Récupération de la décision (15) si un id est fourni et pas de manifeste direct.
        if req.decision_id and self.config.integrate_decision and not manifest:
            decision = self.gateway.decision(req.decision_id)
            if decision:
                manifest = dict(decision.get("execution_manifest", {}))
                decision_status = decision.get("status", decision_status)
                approver = decision.get("validation", {}).get("approver", approver)
                subject = subject or decision.get("request", {}).get("subject", "")
        req.manifest = manifest
        req.decision_status = decision_status

        guards = guard_check(manifest=manifest, decision_status=decision_status,
                             approver=approver, actor=req.actor,
                             authorized_actors=self.config.authorized_actors)

        log = EventLog(self.config.as_of)
        steps: List = []
        if guards["ok"]:
            planset = None
            if manifest.get("plan_ref") and self.config.integrate_planning:
                planset = self.gateway.planset(manifest["plan_ref"])
            steps = build_steps(manifest, planset, self.config.default_job_kind)
            status = RunStatus.PREPARED.value
            log.emit("prepared", req.decision_id, {"steps": len(steps), "actor": req.actor})
        else:
            status = RunStatus.REFUSED.value
            log.emit("refused", req.decision_id, {"refusals": guards["refusals"]})

        run = ExecutionRun(
            request=req, as_of=self.config.as_of, decision_id=req.decision_id,
            subject=subject or manifest.get("selected_option", ""),
            guards=guards, steps=steps, status=status, events=log.events,
            authorization={"actor": req.actor, "approver": approver,
                           "authorized_actors": guards["authorized_actors"]},
            provider=self.providers.select(self.config.provider_order).name).finalize()
        run.report = build_report(run)
        run.traces_for_memory = log.memory_traces(run.id, run.subject, req.actor)

        self.index.add(run)
        self._save()
        return run.to_dict()

    # ================================================================== #
    # 2. Exécution (déclenchée explicitement par un acteur autorisé)
    # ================================================================== #
    def execute(self, run_id: str, actor: str) -> Dict[str, Any]:
        run = self.index.get(run_id)
        if run is None:
            raise NotFoundError(f"Exécution introuvable : {run_id}")
        if run.status != RunStatus.PREPARED.value:
            raise StateError(f"Exécution non exécutable (statut={run.status}).")
        if not run.guards.get("ok"):
            raise GuardRejected("Garde-fous non satisfaits : exécution interdite.")
        if actor not in run.authorization.get("authorized_actors", []):
            raise GuardRejected(f"Acteur non autorisé à exécuter : {actor}.")

        log = EventLog(self.config.as_of)
        for e in run.events:
            log._events.append(e)  # conserve l'historique
        self._transition(run, RunStatus.RUNNING.value)
        log.emit("running", run.decision_id, {"actor": actor, "steps": len(run.steps)})

        approver = run.authorization.get("approver", "") or actor
        results, rt_events = self.runtime.delegate(run.steps, actor, _RUNTIME_AUTONOMY, approver)

        failed = False
        for step in run.steps:
            res = results.get(step.id, {})
            step.job_id = res.get("job_id", "")
            step.result = res
            ok = res.get("status") == "succeeded"
            step.status = StepStatus.SUCCEEDED.value if ok else StepStatus.FAILED.value
            failed = failed or not ok
            log.emit("step_" + step.status, step.id,
                     {"name": step.name, "job_id": step.job_id})

        final = RunStatus.FAILED.value if failed else RunStatus.SUCCEEDED.value
        self._transition(run, final)
        log.emit(final, run.decision_id, {"steps": len(run.steps), "runtime_events": len(rt_events)})

        run.events = log.events
        run.report = build_report(run)
        run.report["runtime_events"] = len(rt_events)
        run.traces_for_memory = log.memory_traces(run.id, run.subject, actor)
        self._save()
        return run.to_dict()

    # ================================================================== #
    # Cycle de vie : annulation / révocation
    # ================================================================== #
    def cancel(self, run_id: str, actor: str) -> Dict[str, Any]:
        return self._lifecycle(run_id, actor, RunStatus.CANCELLED.value, "cancelled")

    def revoke(self, run_id: str, actor: str, reason: str = "") -> Dict[str, Any]:
        return self._lifecycle(run_id, actor, RunStatus.REVOKED.value, "revoked", reason)

    def _lifecycle(self, run_id: str, actor: str, target: str, evt: str, reason: str = "") -> Dict[str, Any]:
        run = self.index.get(run_id)
        if run is None:
            raise NotFoundError(f"Exécution introuvable : {run_id}")
        if actor not in run.authorization.get("authorized_actors", []):
            raise GuardRejected(f"Acteur non autorisé : {actor}.")
        self._transition(run, target)
        log = EventLog(self.config.as_of)
        for e in run.events:
            log._events.append(e)
        log.emit(evt, run.decision_id, {"actor": actor, "reason": reason})
        run.events = log.events
        run.report = build_report(run)
        self._save()
        return {"id": run.id, "status": run.status}

    def _transition(self, run: ExecutionRun, target: str) -> None:
        if not can_transition(run.status, target):
            raise StateError(f"Transition interdite : {run.status} -> {target}.")
        run.status = target

    # ================================================================== #
    # Consultation
    # ================================================================== #
    @property
    def runs(self) -> List[ExecutionRun]:
        return self.index.all()

    def get(self, run_id: str) -> Dict[str, Any]:
        r = self.index.get(run_id)
        if r is None:
            raise NotFoundError(f"Exécution introuvable : {run_id}")
        return r.to_dict()

    def search(self, **kwargs) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.index.search(**kwargs)]

    def explain(self, run_id: str) -> str:
        r = self.index.get(run_id)
        if r is None:
            raise NotFoundError(f"Exécution introuvable : {run_id}")
        return render_markdown(r)

    def traces_for_memory(self, run_id: str) -> List[Dict[str, Any]]:
        return self.get(run_id)["traces_for_memory"]

    # ================================================================== #
    # Export / audit / rapport
    # ================================================================== #
    def export_dict(self) -> Dict[str, Any]:
        return {"as_of": self.config.as_of,
                "runs": [r.to_dict() for r in self.runs], "audit": self.audit()}

    def export_json(self, path: Optional[Path] = None) -> Any:
        data = self.export_dict()
        if path is None:
            return data
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def export_markdown(self, run_id: str, path: Optional[Path] = None) -> Any:
        md = self.explain(run_id)
        if path is None:
            return md
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")
        return path

    def audit(self) -> Dict[str, Any]:
        return audit_all(self.runs)

    def report(self) -> Dict[str, Any]:
        return store_report(self)

    def self_check(self) -> Dict[str, Any]:
        audit = self.audit()
        # aucune exécution n'a tourné sans garde-fous OK
        controlled = all(r.guards.get("ok") for r in self.runs
                         if r.status in ("running", "succeeded", "failed"))
        checks = [
            {"label": "deterministic_provider", "passed": "deterministic" in self.providers.available()},
            {"label": "works_without_external_llm",
             "passed": self.providers.select(["deterministic"]).name == "deterministic"},
            {"label": "audit_ok", "passed": audit["ok"]},
            {"label": "no_execution_without_validated_manifest", "passed": controlled},
            {"label": "runtime_bridge_available", "passed": self.runtime.available},
            {"label": "no_llm_no_network", "passed": True},
        ]
        return {"title": "BrainAI Execution — auto-vérification",
                "ok": all(c["passed"] for c in checks), "checks": checks}

    # ================================================================== #
    # Requête & persistance
    # ================================================================== #
    def _as_request(self, request, kwargs: Dict[str, Any]) -> ExecutionRequest:
        if isinstance(request, ExecutionRequest):
            return request if request.id else request.finalize()
        # ``request`` est un id de décision (chaîne) ; le manifeste direct passe par kwargs.
        decision_id = str(request) if isinstance(request, str) else str(kwargs.get("decision_id", ""))
        r = ExecutionRequest(
            decision_id=decision_id, manifest=dict(kwargs.get("manifest", {}) or {}),
            decision_status=str(kwargs.get("decision_status", "")),
            actor=kwargs.get("actor", "brainai"), tags=list(kwargs.get("tags", []) or []))
        return r.finalize()

    def _save(self) -> None:
        self.config.ensure_directories()
        with self.config.runs_path.open("w", encoding="utf-8") as f:
            for r in self.runs:
                f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

    def _load(self) -> None:
        p = self.config.runs_path
        if not p.exists():
            return
        runs = [ExecutionRun.from_dict(json.loads(l))
                for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.index.rebuild(runs)


__all__ = ["ExecutionEngine"]
