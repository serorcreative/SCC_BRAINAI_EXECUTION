"""Tests des garde-fous — le cœur du contrôle d'exécution."""

from __future__ import annotations

from tests.conftest import VALID_MANIFEST


def _prep(engine, **over):
    m = dict(VALID_MANIFEST); m.update(over.pop("manifest", {}))
    kw = dict(decision_status="validated", approver="frederique", actor="frederique",
              subject="Test")
    kw.update(over)
    return engine.prepare("", manifest=m, **kw)


def test_validated_manifest_prepares(prepared):
    assert prepared["status"] == "prepared"
    assert prepared["guards"]["ok"] is True
    assert len(prepared["steps"]) == 1


def test_proposed_decision_refused(engine):
    r = _prep(engine, decision_status="proposed")
    assert r["status"] == "refused"
    assert "decision_validated" in r["guards"]["refusals"]


def test_rejected_decision_refused(engine):
    r = _prep(engine, decision_status="rejected")
    assert r["status"] == "refused"


def test_revoked_decision_refused(engine):
    r = _prep(engine, decision_status="revoked")
    assert r["status"] == "refused"


def test_execution_status_must_be_not_executed(engine):
    r = _prep(engine, manifest={"execution_status": "succeeded"})
    assert r["status"] == "refused"
    assert "execution_status_not_executed" in r["guards"]["refusals"]


def test_sovereign_manifest_refused(engine):
    r = _prep(engine, manifest={"sovereign": True})
    assert r["status"] == "refused"
    assert "not_sovereign" in r["guards"]["refusals"]


def test_missing_human_validation_refused(engine):
    r = _prep(engine, approver="")
    assert r["status"] == "refused"
    assert "human_validation_present" in r["guards"]["refusals"]


def test_unauthorized_actor_refused(engine):
    r = _prep(engine, actor="intrus")
    assert r["status"] == "refused"
    assert "actor_authorized" in r["guards"]["refusals"]


def test_refused_run_has_no_steps(engine):
    r = _prep(engine, decision_status="proposed")
    assert r["steps"] == []
