"""Rapports d'exécution — synthèse d'une exécution et du registre."""

from __future__ import annotations

from typing import Any, Dict, List

from scc_brainai_execution.core.model import ExecutionRun, StepStatus


def build_report(run: ExecutionRun) -> Dict[str, Any]:
    by_status: Dict[str, int] = {}
    for s in run.steps:
        by_status[s.status] = by_status.get(s.status, 0) + 1
    return {
        "run_id": run.id, "decision_id": run.decision_id, "subject": run.subject,
        "status": run.status,
        "steps_total": len(run.steps),
        "steps_by_status": dict(sorted(by_status.items())),
        "succeeded": by_status.get(StepStatus.SUCCEEDED.value, 0),
        "failed": by_status.get(StepStatus.FAILED.value, 0),
        "guards_ok": run.guards.get("ok"),
        "events": len(run.events),
        "note": "Exécution pilotée sous contrôle ; déléguée au Runtime ; jamais appliquée sans manifeste validé.",
    }


def store_report(engine) -> Dict[str, Any]:
    runs = engine.runs
    by_status: Dict[str, int] = {}
    for r in runs:
        by_status[r.status] = by_status.get(r.status, 0) + 1
    audit = engine.audit()
    return {
        "as_of": engine.config.as_of,
        "total_runs": len(runs),
        "by_status": dict(sorted(by_status.items())),
        "audit_ok": audit["ok"],
        "runs": [build_report(r) for r in runs],
        "safety_note": "Aucune exécution sans manifeste validé ni autorisation explicite.",
    }


def render_markdown(run: ExecutionRun) -> str:
    lines: List[str] = [
        f"# Exécution — {run.id}",
        "",
        f"> `as_of` : {run.as_of} · fournisseur : {run.provider} · statut : **{run.status}**",
        "",
        f"**Sujet** : {run.subject}  ·  **Décision** : {run.decision_id or '—'}",
        "",
        "## Garde-fous", "",
        f"- ok : **{run.guards.get('ok')}**",
    ]
    for k, v in sorted((run.guards.get("checks", {})).items()):
        lines.append(f"  - {k} : {'✅' if v else '❌'}")
    if run.guards.get("refusals"):
        lines.append(f"- refus : {run.guards['refusals']}")
    lines += ["", "## Étapes", "",
              "| # | Étape | Type | Statut | Job |", "|---|-------|------|--------|-----|"]
    for s in run.steps:
        lines.append(f"| {s.order} | {s.name} | {s.kind} | {s.status} | {s.job_id or '—'} |")
    lines += ["", "## Événements", ""]
    for e in run.events:
        lines.append(f"- `{e['type']}` {e.get('subject','')} — {e.get('payload',{})}")
    lines += ["", "## Traces pour Memory (plus tard)", "",
              f"- {len(run.traces_for_memory)} trace(s) neutre(s) prêtes pour une future ingestion Memory.",
              "",
              "> Exécution **sous contrôle** : aucune exécution sans manifeste validé, "
              "aucune exécution automatique non autorisée. Le Runtime est le seul exécutant technique.",
              "",
              "*Exécution déterministe BrainAI — sans réseau ni LLM obligatoire.*"]
    return "\n".join(lines) + "\n"


__all__ = ["build_report", "store_report", "render_markdown"]
