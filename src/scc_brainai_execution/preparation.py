"""Préparation — transforme un manifeste (et un plan éventuel) en étapes d'exécution.

Chaque étape est matérialisée comme un **job Runtime** (type hermétique par défaut).
Si le manifeste référence un plan (``plan_ref``), les tâches du plan ordonné
deviennent les étapes ; sinon une étape unique matérialise l'option retenue.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from scc_brainai_execution.core.model import ExecutionStep


def build_steps(manifest: Dict[str, Any], planset: Optional[Dict[str, Any]],
                default_kind: str) -> List[ExecutionStep]:
    steps: List[ExecutionStep] = []
    src_manifest = f"decision_manifest:{manifest.get('selected_option_id', '')}"

    if planset:
        rec = planset.get("recommended", {})
        plan_id = rec.get("id", planset.get("id", ""))
        for m in rec.get("executable_manifest", []):
            steps.append(ExecutionStep(
                order=int(m.get("order", 0)),
                name=m.get("title", "tâche"),
                kind=default_kind,
                params={"action": m.get("title", ""), "task_id": m.get("task_id", ""),
                        "phase": m.get("phase", "")},
                sources=[src_manifest, f"plan:{plan_id}"]).finalize())
    else:
        steps.append(ExecutionStep(
            order=1, name=manifest.get("selected_option", "décision"), kind=default_kind,
            params={"action": manifest.get("selected_option", ""),
                    "option_id": manifest.get("selected_option_id", "")},
            sources=[src_manifest]).finalize())

    steps.sort(key=lambda s: (s.order, s.id))
    return steps


__all__ = ["build_steps"]
