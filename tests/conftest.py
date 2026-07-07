"""Fixtures des tests d'exécution (isolées, déterministes).

Un manifeste validé direct est utilisé (hermétique) ; un test dédié vérifie
l'intégration réelle Decision→Execution→Runtime.
"""

from __future__ import annotations

import pytest

from scc_brainai_execution.core.config import ExecutionConfig
from scc_brainai_execution.engine import ExecutionEngine

VALID_MANIFEST = {
    "selected_option": "Publier en beta privée", "selected_option_id": "opt_x",
    "origin": "manual", "plan_ref": None, "executable": True,
    "execution_status": "not_executed", "requires_human_validation": True,
    "sovereign": False, "preconditions": ["Validation humaine explicite."],
    "success_criteria": ["Objectif atteint."], "failure_criteria": ["Rollback nécessaire."],
    "abort_conditions": ["Contexte changé."],
}


@pytest.fixture
def config(tmp_path):
    return ExecutionConfig(data_dir=tmp_path / "data", authorized_actors=["frederique"],
                           integrate_decision=False, integrate_planning=False)


@pytest.fixture
def engine(config):
    return ExecutionEngine(config=config)


@pytest.fixture
def prepared(engine):
    return engine.prepare("", manifest=VALID_MANIFEST, decision_status="validated",
                          approver="frederique", actor="frederique", subject="Publier la beta")
