"""SCC BrainAI Execution — couche officielle d'exécution de BrainAI.

**Reçoit un manifeste décisionnel validé et pilote son exécution sous contrôle**,
en déléguant au Runtime via ses interfaces publiques. Deux temps : ``prepare``
(garde-fous + étapes) puis ``execute`` (déclenchement explicite par un acteur
autorisé). Suit l'état, journalise, produit un rapport et des traces pour Memory.

Execution n'est ni Runtime (exécutant technique), ni Kernel (orchestration), ni
Planning (plans), ni Decision (décisions). Il **réutilise** leurs interfaces
publiques, sans modifier aucun composant.

Garde-fous : aucune exécution sans manifeste **validated** ; aucune exécution si
``execution_status != not_executed`` ; aucune exécution automatique non autorisée ;
aucune auto-modification ; traçabilité complète. Fonctionne **sans aucune IA**
(pilotage déterministe ; LLM optionnel pour diagnostic/rapports). Stdlib pur, sans
réseau, déterministe.
"""

from __future__ import annotations

__version__ = "1.0.0"

from scc_brainai_execution.core.config import ExecutionConfig, load_config
from scc_brainai_execution.core.model import (
    ExecutionRequest,
    ExecutionRun,
    ExecutionStep,
    RunStatus,
)
from scc_brainai_execution.engine import ExecutionEngine
from scc_brainai_execution.providers.registry import ProviderRegistry

__all__ = [
    "__version__",
    "ExecutionEngine",
    "ExecutionConfig",
    "load_config",
    "ExecutionRequest",
    "ExecutionStep",
    "ExecutionRun",
    "RunStatus",
    "ProviderRegistry",
]
