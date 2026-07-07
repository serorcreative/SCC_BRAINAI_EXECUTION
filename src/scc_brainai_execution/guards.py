"""Garde-fous d'exécution — le cœur du contrôle.

Aucune exécution n'est permise sans qu'un manifeste **validé** et **autorisé** ne
franchisse tous les garde-fous :

* le manifeste doit exister ;
* la décision doit être **validated** (ni proposed, ni rejected, ni revoked) ;
* ``execution_status`` doit être **not_executed** ;
* le manifeste ne doit pas être **sovereign** ;
* si le manifeste requiert une validation humaine, un **approbateur** doit exister ;
* l'acteur déclencheur doit être **autorisé**.
"""

from __future__ import annotations

from typing import Any, Dict, List


def check(*, manifest: Dict[str, Any], decision_status: str, approver: str,
          actor: str, authorized_actors: List[str]) -> Dict[str, Any]:
    allowed = set(authorized_actors) | ({approver} if approver else set())
    checks = {
        "manifest_present": bool(manifest),
        "decision_validated": decision_status == "validated",
        "execution_status_not_executed": manifest.get("execution_status") == "not_executed",
        "not_sovereign": manifest.get("sovereign") is False,
        "human_validation_present": (not manifest.get("requires_human_validation")) or bool(approver),
        "actor_authorized": actor in allowed,
    }
    refusals = sorted(k for k, v in checks.items() if not v)
    return {"ok": not refusals, "checks": checks, "refusals": refusals,
            "authorized_actors": sorted(allowed)}


__all__ = ["check"]
