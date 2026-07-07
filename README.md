# SCC BrainAI Execution

**Couche officielle d'exécution de BrainAI.**

Execution **reçoit un manifeste décisionnel validé et pilote son exécution sous
contrôle**, en déléguant au **Runtime** via ses interfaces publiques. Il n'est ni
Runtime (l'exécutant technique), ni Kernel (orchestration), ni Planning (plans), ni
Decision (décisions) :

- **Runtime** exécute des jobs techniques. · **Kernel** orchestre. · **Planning**
  prépare des plans. · **Decision** formalise des décisions gouvernées.
- **Execution** reçoit un manifeste **validé**, vérifie les garde-fous, le transforme
  en **étapes**, **délègue au Runtime**, suit l'état, journalise, produit un rapport
  et des **traces exploitables par Memory plus tard**.

> **Garde-fous : aucune exécution sans manifeste validé ; aucune exécution si
> `execution_status != not_executed` ; aucune exécution automatique non autorisée ;
> aucune auto-modification ; traçabilité complète.** **Fonctionne sans aucune IA**
> (pilotage déterministe ; LLM optionnel pour diagnostic/rapports). Stdlib pur, sans
> réseau, déterministe.

## Deux temps, sous contrôle

1. **`prepare`** — vérifie les garde-fous (décision `validated`, `not_executed`, non
   souverain, validation humaine présente, acteur autorisé) et transforme le manifeste
   en étapes. Si un garde-fou refuse → statut **`refused`**, aucune exécution.
2. **`execute`** — **déclenchée explicitement par un acteur autorisé** (jamais
   automatique) ; délègue chaque étape au **Runtime** (seul exécutant technique).

## Réutilisation, jamais duplication

Execution lit la décision de **Decision (15)**, les étapes de **Planning (14)**, et
**délègue au Runtime (07)** — tout via **interfaces publiques**, sans modifier aucun
composant. Le manifeste de la décision est **lu, jamais muté**.

## Installation

```bash
cd 16_BRAINAI_EXECUTION
python -m pip install -e .        # expose la commande `scc-brain-execution`
```

Aucune dépendance externe.

## Utilisation (CLI)

```bash
# À partir d'une décision validée (Decision 15) :
scc-brain-execution prepare <decision_id> --actor frederique
scc-brain-execution execute <run_id> --by frederique       # acteur autorisé requis
scc-brain-execution explain <run_id>                        # rapport lisible (Markdown)
scc-brain-execution cancel <run_id> --by frederique
scc-brain-execution revoke <run_id> --by frederique --reason "contexte changé"
scc-brain-execution traces <run_id>                         # traces pour Memory (plus tard)
scc-brain-execution report | audit | self-check | providers
# Manifeste direct (hermétique) :
scc-brain-execution prepare --manifest-file m.json --decision-status validated \
    --approver frederique --actor frederique --subject "Publier"
```

## Utilisation (Python)

```python
from scc_brainai_execution import ExecutionEngine

engine = ExecutionEngine()
run = engine.prepare(decision_id, actor="frederique")   # garde-fous
if run["status"] == "prepared":
    engine.execute(run["id"], actor="frederique")        # déclenchement autorisé
```

## Composants

`ExecutionEngine` · `ExecutionRequest` · `ExecutionStep` · `ExecutionRun` ·
`RuntimeBridge` (délégation Runtime) · `SourceGateway` (Decision/Planning) ·
`ProviderRegistry` (LLM optionnel : diagnostic/rapports).

Détails : [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) ·
[`docs/EXECUTION_MODEL.md`](docs/EXECUTION_MODEL.md) ·
[`docs/GUARDS_CONTROL.md`](docs/GUARDS_CONTROL.md) ·
[`docs/GOVERNANCE_SAFETY.md`](docs/GOVERNANCE_SAFETY.md).

## Tests

```bash
python -m pytest -q      # 28 tests (déterministes ; 2 intégrations Decision→Runtime réelles)
```
