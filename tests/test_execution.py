"""Tests d'exécution : délégation Runtime, suivi d'état, cycle de vie, audit."""

from __future__ import annotations

import pytest

from scc_brainai_execution.core.errors import GuardRejected, StateError


def test_execute_delegates_to_runtime(engine, prepared):
    done = engine.execute(prepared["id"], actor="frederique")
    assert done["status"] == "succeeded"
    step = done["steps"][0]
    assert step["status"] == "succeeded"
    assert step["job_id"]                       # un job Runtime a été soumis
    assert done["report"]["steps_by_status"].get("succeeded") == 1


def test_execute_requires_authorized_actor(engine, prepared):
    with pytest.raises(GuardRejected):
        engine.execute(prepared["id"], actor="intrus")


def test_refused_run_cannot_execute(engine):
    from tests.conftest import VALID_MANIFEST
    r = engine.prepare("", manifest=VALID_MANIFEST, decision_status="proposed",
                       approver="frederique", actor="frederique")
    with pytest.raises(StateError):
        engine.execute(r["id"], actor="frederique")


def test_cannot_execute_twice(engine, prepared):
    engine.execute(prepared["id"], actor="frederique")
    with pytest.raises(StateError):
        engine.execute(prepared["id"], actor="frederique")


def test_events_journaled(engine, prepared):
    done = engine.execute(prepared["id"], actor="frederique")
    types = {e["type"] for e in done["events"]}
    assert {"prepared", "running", "succeeded"} <= types


def test_traces_for_memory(engine, prepared):
    done = engine.execute(prepared["id"], actor="frederique")
    traces = done["traces_for_memory"]
    assert traces
    assert all(t["kind"] == "event" and t["subtype"].startswith("execution.") for t in traces)


def test_cancel(engine, prepared):
    engine.cancel(prepared["id"], "frederique")
    assert engine.get(prepared["id"])["status"] == "cancelled"


def test_revoke_after_execute(engine, prepared):
    engine.execute(prepared["id"], actor="frederique")
    engine.revoke(prepared["id"], "frederique", "contexte changé")
    assert engine.get(prepared["id"])["status"] == "revoked"


def test_lifecycle_requires_authorized(engine, prepared):
    with pytest.raises(GuardRejected):
        engine.cancel(prepared["id"], "intrus")


def test_audit_and_self_check(engine, prepared):
    engine.execute(prepared["id"], actor="frederique")
    assert engine.audit()["ok"] is True
    sc = engine.self_check()
    assert sc["ok"] is True
    labels = {c["label"] for c in sc["checks"]}
    assert {"no_execution_without_validated_manifest", "no_llm_no_network"} <= labels


def test_audit_detects_step_tampering(engine, prepared):
    engine.execute(prepared["id"], actor="frederique")
    run = engine.index.get(prepared["id"])
    run.steps[0].name = "TAMPERED"
    a = engine.audit()
    assert a["per_run"][prepared["id"]]["integrity"]["ok"] is False
