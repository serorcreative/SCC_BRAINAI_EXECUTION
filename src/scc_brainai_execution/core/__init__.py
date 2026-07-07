"""Noyau de la couche d'exécution : config, erreurs, modèle."""

from __future__ import annotations

from scc_brainai_execution.core.clock import canonical, digest, short_id
from scc_brainai_execution.core.config import ExecutionConfig, load_config
from scc_brainai_execution.core.errors import (
    ConfigError,
    ExecutionError,
    GuardRejected,
    NotFoundError,
    RequestError,
    SourceUnavailable,
    StateError,
)
from scc_brainai_execution.core.model import (
    ExecutionRequest,
    ExecutionRun,
    ExecutionStep,
    RunStatus,
    StepStatus,
    can_transition,
)

__all__ = [
    "canonical", "digest", "short_id",
    "ExecutionConfig", "load_config",
    "ExecutionError", "ConfigError", "SourceUnavailable", "GuardRejected",
    "NotFoundError", "RequestError", "StateError",
    "RunStatus", "StepStatus", "can_transition",
    "ExecutionStep", "ExecutionRequest", "ExecutionRun",
]
