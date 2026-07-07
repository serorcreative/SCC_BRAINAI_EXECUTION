"""Hiérarchie d'exceptions de la couche d'exécution BrainAI."""

from __future__ import annotations


class ExecutionError(Exception):
    """Erreur de base de la couche d'exécution."""


class ConfigError(ExecutionError):
    """Configuration absente, illisible ou invalide."""


class SourceUnavailable(ExecutionError):
    """Une source (Decision, Runtime, Planning) est indisponible."""


class GuardRejected(ExecutionError):
    """Un garde-fou a refusé l'exécution (manifeste non validé, non autorisé…)."""


class NotFoundError(ExecutionError):
    """Exécution introuvable."""


class RequestError(ExecutionError):
    """Demande d'exécution mal formée (ni décision, ni manifeste)."""


class StateError(ExecutionError):
    """Transition d'état d'exécution interdite."""


__all__ = ["ExecutionError", "ConfigError", "SourceUnavailable", "GuardRejected",
           "NotFoundError", "RequestError", "StateError"]
