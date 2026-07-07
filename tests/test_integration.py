"""Test d'intégration : Decision (validée) → Execution → Runtime (interfaces publiques).

Construit une décision réelle (Decision 15), la valide humainement, puis prépare et
exécute via Execution qui délègue au Runtime réel. Vérifie qu'une décision NON validée
est refusée. Ignoré proprement si les couches ne sont pas localisables.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_DECISION = _ROOT / "15_BRAINAI_DECISION" / "src"
_RUNTIME = _ROOT / "07_RUNTIME" / "src"

_available = _DECISION.exists() and _RUNTIME.exists()
if _available:
    for p in (_DECISION, _RUNTIME):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

pytestmark = pytest.mark.skipif(not _available, reason="Decision/Runtime non localisables.")


def _decision(tmp_path):
    from scc_brainai_decision.core.config import DecisionConfig
    from scc_brainai_decision.engine import DecisionEngine
    eng = DecisionEngine(config=DecisionConfig(data_dir=tmp_path / "dec", integrate_reasoning=False,
                                               integrate_planning=False, integrate_learning=False))
    rec = eng.decide("Faut-il publier ?",
                     options=[{"name": "Publier", "impact": 0.7, "risk": 0.3, "reversibility": 0.6},
                              {"name": "Différer", "impact": 0.3, "risk": 0.1, "reversibility": 0.9}])
    return eng, rec["id"]


def test_execute_from_validated_decision(tmp_path):
    from scc_brainai_execution.core.config import ExecutionConfig
    from scc_brainai_execution.engine import ExecutionEngine
    from scc_brainai_execution.sources.source_gateway import SourceGateway

    dec_eng, dec_id = _decision(tmp_path)
    dec_eng.validate(dec_id, "frederique", "go")   # validation humaine

    cfg = ExecutionConfig(data_dir=tmp_path / "exec", authorized_actors=["frederique"],
                          integrate_decision=True, integrate_planning=False)
    eng = ExecutionEngine(config=cfg, gateway=SourceGateway(cfg, decision_engine=dec_eng))
    run = eng.prepare(dec_id, actor="frederique")
    assert run["status"] == "prepared"
    assert run["guards"]["ok"] is True

    done = eng.execute(run["id"], actor="frederique")
    assert done["status"] == "succeeded"
    assert done["steps"][0]["job_id"]                 # délégué au Runtime réel
    assert eng.audit()["ok"] is True


def test_unvalidated_decision_refused(tmp_path):
    from scc_brainai_execution.core.config import ExecutionConfig
    from scc_brainai_execution.engine import ExecutionEngine
    from scc_brainai_execution.sources.source_gateway import SourceGateway

    dec_eng, dec_id = _decision(tmp_path)   # NON validée (proposed)
    cfg = ExecutionConfig(data_dir=tmp_path / "exec", authorized_actors=["frederique"],
                          integrate_decision=True, integrate_planning=False)
    eng = ExecutionEngine(config=cfg, gateway=SourceGateway(cfg, decision_engine=dec_eng))
    run = eng.prepare(dec_id, actor="frederique")
    assert run["status"] == "refused"
    assert "decision_validated" in run["guards"]["refusals"]
