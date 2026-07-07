"""CLI de la couche d'exécution BrainAI (``scc-brain-execution``).

Préparer (garde-fous), **exécuter** (déclenchement explicite autorisé), annuler,
révoquer, expliquer, auditer. Sortie JSON déterministe. Aucune commande n'exécute
sans manifeste validé ni sans acteur autorisé.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from scc_brainai_execution import __version__
from scc_brainai_execution.core.config import load_config
from scc_brainai_execution.core.errors import ExecutionError
from scc_brainai_execution.engine import ExecutionEngine


def _out(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _engine(args) -> ExecutionEngine:
    return ExecutionEngine(config=load_config(args.config))


def cmd_prepare(args) -> int:
    eng = _engine(args)
    kwargs: Dict[str, Any] = {"actor": args.actor}
    if args.manifest_file:
        manifest = json.loads(Path(args.manifest_file).read_text(encoding="utf-8"))
        kwargs.update(manifest=manifest, decision_status=args.decision_status or "",
                      approver=args.approver or "", subject=args.subject or "")
        request = ""
    else:
        request = args.decision or ""
        kwargs.update(approver=args.approver or "", subject=args.subject or "")
    try:
        _out(eng.prepare(request, **kwargs)); return 0
    except ExecutionError as exc:
        _out({"error": str(exc)}); return 1


def cmd_execute(args) -> int:
    try:
        _out(_engine(args).execute(args.id, actor=args.by)); return 0
    except ExecutionError as exc:
        _out({"error": str(exc)}); return 1


def _lifecycle(args, action: str) -> int:
    eng = _engine(args)
    try:
        if action == "revoke":
            _out(eng.revoke(args.id, args.by, args.reason))
        else:
            _out(eng.cancel(args.id, args.by))
        return 0
    except ExecutionError as exc:
        _out({"error": str(exc)}); return 1


def cmd_get(args) -> int:
    try:
        _out(_engine(args).get(args.id)); return 0
    except ExecutionError as exc:
        _out({"error": str(exc)}); return 1


def cmd_explain(args) -> int:
    try:
        print(_engine(args).explain(args.id)); return 0
    except ExecutionError as exc:
        _out({"error": str(exc)}); return 1


def cmd_traces(args) -> int:
    try:
        _out(_engine(args).traces_for_memory(args.id)); return 0
    except ExecutionError as exc:
        _out({"error": str(exc)}); return 1


def cmd_search(args) -> int:
    _out(_engine(args).search(status=args.status, text=args.text, limit=int(args.limit))); return 0


def cmd_report(args) -> int:
    _out(_engine(args).report()); return 0


def cmd_audit(args) -> int:
    a = _engine(args).audit(); _out(a); return 0 if a["ok"] else 1


def cmd_self_check(args) -> int:
    sc = _engine(args).self_check(); _out(sc); return 0 if sc["ok"] else 1


def cmd_providers(args) -> int:
    _out(_engine(args).providers.to_dict()); return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scc-brain-execution",
                                     description="Couche d'exécution de BrainAI (pilotage sous contrôle).")
    parser.add_argument("--version", action="version", version=f"scc-brain-execution {__version__}")
    parser.add_argument("--config", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="Vérifier les garde-fous et préparer les étapes.")
    p.add_argument("decision", nargs="?", default=None, help="id de décision (Decision 15)")
    p.add_argument("--manifest-file", default=None, help="manifeste JSON direct (hermétique)")
    p.add_argument("--decision-status", default=None)
    p.add_argument("--approver", default=None)
    p.add_argument("--subject", default=None)
    p.add_argument("--actor", default="brainai")
    p.set_defaults(func=cmd_prepare)

    p_e = sub.add_parser("execute", help="Exécuter (acteur autorisé requis).")
    p_e.add_argument("id"); p_e.add_argument("--by", required=True)
    p_e.set_defaults(func=cmd_execute)

    p_c = sub.add_parser("cancel", help="Annuler une exécution.")
    p_c.add_argument("id"); p_c.add_argument("--by", required=True)
    p_c.set_defaults(func=lambda a: _lifecycle(a, "cancel"))

    p_rv = sub.add_parser("revoke", help="Révoquer une exécution.")
    p_rv.add_argument("id"); p_rv.add_argument("--by", required=True); p_rv.add_argument("--reason", default="")
    p_rv.set_defaults(func=lambda a: _lifecycle(a, "revoke"))

    p_get = sub.add_parser("get", help="Détail d'une exécution."); p_get.add_argument("id"); p_get.set_defaults(func=cmd_get)
    p_ex = sub.add_parser("explain", help="Rapport lisible (Markdown)."); p_ex.add_argument("id"); p_ex.set_defaults(func=cmd_explain)
    p_tr = sub.add_parser("traces", help="Traces pour Memory (plus tard)."); p_tr.add_argument("id"); p_tr.set_defaults(func=cmd_traces)

    p_s = sub.add_parser("search", help="Recherche d'exécutions.")
    p_s.add_argument("--status", default=None); p_s.add_argument("--text", default=None)
    p_s.add_argument("--limit", default="50"); p_s.set_defaults(func=cmd_search)

    sub.add_parser("report", help="Rapport du registre d'exécutions.").set_defaults(func=cmd_report)
    sub.add_parser("audit", help="Audit (intégrité, traçabilité, sûreté).").set_defaults(func=cmd_audit)
    sub.add_parser("self-check", help="Auto-vérification.").set_defaults(func=cmd_self_check)
    sub.add_parser("providers", help="Fournisseurs d'exécution.").set_defaults(func=cmd_providers)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


__all__ = ["main", "build_parser"]
