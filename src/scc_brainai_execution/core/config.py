"""Configuration de la couche d'exécution BrainAI (JSON, sans dépendance).

L'exécution **reçoit un manifeste décisionnel validé** et **pilote** son exécution
sous contrôle, en **déléguant au Runtime** via ses interfaces publiques. Elle peut
récupérer une décision via Decision (15) et des étapes via Planning (14) — de façon
optionnelle et dégradable. Elle ne possède ni ne modifie aucune autre couche.

Déterminisme : ``as_of`` fige l'horloge du Runtime piloté et les horodatages.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from scc_brainai_execution.core.errors import ConfigError

EXECUTION_ROOT = Path(__file__).resolve().parents[3]      # .../16_BRAINAI_EXECUTION
DEFAULT_SCC_ROOT = EXECUTION_ROOT.parent                   # .../01_CCSC
DEFAULT_CONFIG_PATH = EXECUTION_ROOT / "config" / "execution.json"

DEFAULT_AS_OF = "2026-07-06T00:00:00+00:00"


@dataclass
class ExecutionConfig:
    execution_root: Path = EXECUTION_ROOT
    scc_root: Path = DEFAULT_SCC_ROOT
    data_dir: Path = EXECUTION_ROOT / "data"
    as_of: str = DEFAULT_AS_OF
    # Acteurs autorisés à déclencher une exécution (l'approbateur de la décision est
    # toujours implicitement autorisé). Aucune exécution automatique non autorisée.
    authorized_actors: List[str] = field(default_factory=list)
    # Type de job Runtime par défaut pour matérialiser une étape (hermétique).
    default_job_kind: str = "echo"
    integrate_decision: bool = True
    integrate_planning: bool = True
    provider_order: List[str] = field(default_factory=lambda: ["deterministic"])
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def decision_src(self) -> Path:
        return self.scc_root / "15_BRAINAI_DECISION" / "src"

    @property
    def planning_src(self) -> Path:
        return self.scc_root / "14_BRAINAI_PLANNING" / "src"

    @property
    def runtime_src(self) -> Path:
        return self.scc_root / "07_RUNTIME" / "src"

    @property
    def runs_path(self) -> Path:
        return self.data_dir / "executions.jsonl"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        return {"execution_root": str(self.execution_root), "scc_root": str(self.scc_root),
                "data_dir": str(self.data_dir), "as_of": self.as_of,
                "authorized_actors": list(self.authorized_actors),
                "default_job_kind": self.default_job_kind,
                "integrate_decision": self.integrate_decision,
                "integrate_planning": self.integrate_planning,
                "provider_order": list(self.provider_order)}


def _resolve(base: Path, value: str) -> Path:
    p = Path(value).expanduser()
    return p if p.is_absolute() else (base / p).resolve()


def load_config(path: Optional[Path] = None) -> ExecutionConfig:
    config = ExecutionConfig()
    target = Path(path) if path else DEFAULT_CONFIG_PATH
    if not target.exists():
        if path is not None:
            raise ConfigError(f"Configuration introuvable : {target}")
        return config
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Configuration illisible ({target}) : {exc}") from exc

    base = config.execution_root
    if "scc_root" in raw:
        config.scc_root = _resolve(base, raw["scc_root"])
    paths = raw.get("paths", {})
    if "data_dir" in paths:
        config.data_dir = _resolve(base, paths["data_dir"])
    config.as_of = str(raw.get("as_of", DEFAULT_AS_OF))
    config.authorized_actors = list(raw.get("authorized_actors", []))
    config.default_job_kind = str(raw.get("default_job_kind", "echo"))
    config.integrate_decision = bool(raw.get("integrate_decision", True))
    config.integrate_planning = bool(raw.get("integrate_planning", True))
    config.provider_order = list(raw.get("provider_order", config.provider_order))
    config.extra = dict(raw.get("extra", {}))
    return config


__all__ = ["EXECUTION_ROOT", "DEFAULT_SCC_ROOT", "DEFAULT_AS_OF", "ExecutionConfig", "load_config"]
