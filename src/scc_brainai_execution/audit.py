"""Audit de l'exécution : intégrité, traçabilité, sûreté (gouvernance).

* **intégrité** : l'empreinte de chaque étape correspond à son contenu ;
* **traçabilité** : chaque étape cite une source ;
* **sûreté** : une exécution n'a pu **s'exécuter** que si les garde-fous étaient
  passés ; une exécution **refusée** n'a lancé aucune étape.
"""

from __future__ import annotations

from typing import Any, Dict, List

from scc_brainai_execution.core.model import ExecutionRun, RunStatus, StepStatus

_EXECUTED = {RunStatus.RUNNING.value, RunStatus.SUCCEEDED.value, RunStatus.FAILED.value}
_RAN_STEP = {StepStatus.RUNNING.value, StepStatus.SUCCEEDED.value, StepStatus.FAILED.value}


def audit_run(run: ExecutionRun) -> Dict[str, Any]:
    integrity_broken = sorted(s.id for s in run.steps if not s.verify())
    untraced = sorted(s.id for s in run.steps if not s.sources)

    safe = True
    reasons: List[str] = []
    if run.status in _EXECUTED and not run.guards.get("ok"):
        safe = False; reasons.append("exécution lancée alors que les garde-fous ont refusé")
    if run.status == RunStatus.REFUSED.value and any(s.status in _RAN_STEP for s in run.steps):
        safe = False; reasons.append("exécution refusée mais des étapes ont été lancées")
    if run.status in _EXECUTED and run.request.decision_status != "validated":
        safe = False; reasons.append("exécution alors que la décision n'est pas validée")

    return {
        "ok": not integrity_broken and not untraced and safe,
        "integrity": {"ok": not integrity_broken, "broken": integrity_broken},
        "traceability": {"ok": not untraced, "untraced": untraced},
        "safety": {"ok": safe, "reasons": reasons, "status": run.status,
                   "guards_ok": run.guards.get("ok")},
        "steps": len(run.steps),
    }


def audit_all(runs: List[ExecutionRun]) -> Dict[str, Any]:
    reports = {r.id: audit_run(r) for r in runs}
    return {"ok": all(x["ok"] for x in reports.values()) if reports else True,
            "count": len(runs), "per_run": reports}


__all__ = ["audit_run", "audit_all"]
