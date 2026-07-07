"""Tests de déterminisme, export, explication et CLI."""

from __future__ import annotations

import json

from scc_brainai_execution.cli import main
from scc_brainai_execution.core.config import ExecutionConfig
from scc_brainai_execution.engine import ExecutionEngine
from tests.conftest import VALID_MANIFEST


def _flow(data_dir):
    eng = ExecutionEngine(config=ExecutionConfig(data_dir=data_dir, authorized_actors=["frederique"],
                                                 integrate_decision=False, integrate_planning=False))
    r = eng.prepare("", manifest=VALID_MANIFEST, decision_status="validated",
                    approver="frederique", actor="frederique", subject="S")
    return eng.execute(r["id"], actor="frederique")


def test_deterministic_execution(tmp_path):
    a = _flow(tmp_path / "a")
    b = _flow(tmp_path / "b")
    assert json.dumps(a, sort_keys=True, ensure_ascii=False) == \
           json.dumps(b, sort_keys=True, ensure_ascii=False)


def test_explain_markdown(engine, prepared):
    engine.execute(prepared["id"], actor="frederique")
    md = engine.explain(prepared["id"])
    for section in ("## Garde-fous", "## Étapes", "## Événements", "## Traces pour Memory"):
        assert section in md
    assert "manifeste validé" in md


def test_export_and_report(engine, prepared, tmp_path):
    engine.execute(prepared["id"], actor="frederique")
    data = engine.export_dict()
    assert data["runs"]
    jp = engine.export_json(tmp_path / "e.json")
    assert jp.exists()
    report = engine.report()
    assert report["total_runs"] == 1
    assert report["by_status"].get("succeeded") == 1


def test_persistence_roundtrip(config):
    e1 = ExecutionEngine(config=config)
    r = e1.prepare("", manifest=VALID_MANIFEST, decision_status="validated",
                   approver="frederique", actor="frederique", subject="S")
    e1.execute(r["id"], actor="frederique")
    e2 = ExecutionEngine(config=config)   # relit depuis le disque
    assert e2.get(r["id"])["status"] == "succeeded"
    assert e2.audit()["ok"] is True


def _cfg_file(tmp_path, manifest):
    cfg = tmp_path / "execution.json"
    cfg.write_text(json.dumps({"paths": {"data_dir": str(tmp_path / "d")},
                               "as_of": "2026-07-06T00:00:00+00:00",
                               "authorized_actors": ["frederique"],
                               "integrate_decision": False, "integrate_planning": False}),
                   encoding="utf-8")
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps(manifest), encoding="utf-8")
    return cfg, mf


def test_cli_prepare_and_execute(tmp_path, capsys):
    cfg, mf = _cfg_file(tmp_path, VALID_MANIFEST)
    rc = main(["--config", str(cfg), "prepare", "--manifest-file", str(mf),
               "--decision-status", "validated", "--approver", "frederique",
               "--actor", "frederique", "--subject", "Test"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["status"] == "prepared"
    rid = out["id"]
    rc = main(["--config", str(cfg), "execute", rid, "--by", "frederique"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["status"] == "succeeded"


def test_cli_prepare_refused_returns_prepared_with_refused_status(tmp_path, capsys):
    cfg, mf = _cfg_file(tmp_path, {**VALID_MANIFEST, "sovereign": True})
    rc = main(["--config", str(cfg), "prepare", "--manifest-file", str(mf),
               "--decision-status", "validated", "--approver", "frederique", "--actor", "frederique"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["status"] == "refused"
    assert "not_sovereign" in out["guards"]["refusals"]
