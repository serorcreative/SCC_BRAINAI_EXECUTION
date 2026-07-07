# Architecture de BrainAI Execution

## 1. Position dans SCC

Execution (`16`) est la couche qui **pilote l'exécution d'une décision validée**.
Elle se situe entre Decision (15) et le Runtime (07) : elle transforme un manifeste
décisionnel validé en étapes et **délègue leur exécution technique au Runtime**.

```
   Decision (15)          Planning (14)
   (manifeste validé)     (étapes de plan éventuelles)
        \                     \
         \ interfaces publiques (lecture)
          ─────────────────────────────────
   ▶ Execution (16) ── ExecutionEngine : garde-fous -> étapes -> DÉLÉGATION
        │                                        │
        │  data/executions.jsonl                 ▼  interfaces publiques
        │  (registre — seul espace d'écriture)  Runtime (07) : jobs techniques
        └──▶ traces_for_memory (pour Memory 11, plus tard)
```

## 2. Distinction des rôles

| Couche | Rôle |
|--------|------|
| Runtime (07) | **exécute des jobs techniques** (seul exécutant) |
| Kernel (10) | orchestre |
| Planning (14) | prépare des plans |
| Decision (15) | formalise des décisions gouvernées |
| **Execution (16)** | **reçoit un manifeste validé et pilote son exécution sous contrôle** |

Aucune duplication : Execution **ne fait rien techniquement** ; elle **contrôle** et
**délègue** au Runtime. C'est le chef d'orchestre *contrôlé* d'une décision validée.

## 3. Chaîne d'exécution (déterministe, en deux temps)

```
prepare(decision) :
  fetch décision (15) -> manifeste + statut + approbateur
  guards.check()      -> validated ? not_executed ? non souverain ? validation humaine ? acteur autorisé ?
  build_steps()       -> étapes (option, ou tâches du plan)
  => statut PREPARED  (ou REFUSED si un garde-fou refuse)

execute(run, actor) : (déclenchement explicite, acteur autorisé)
  RuntimeBridge.delegate(steps) -> un job Runtime par étape (horloge injectée)
  suivi d'état, journal d'événements
  => statut SUCCEEDED | FAILED ; rapport + traces_for_memory
```

Chaque étape est **pure** : mêmes entrées ⇒ même exécution (le Runtime est piloté
avec une horloge et une fabrique d'identifiants **déterministes**).

## 4. Composants

```
core/        config (as_of, acteurs autorisés) · errors · clock (digest) · model (Request/Step/Run)
providers/   base · deterministic (défaut) · external (Claude/ChatGPT/Gemini : diagnostic) · registry
sources/     runtime_bridge (délégation Runtime) · source_gateway (Decision/Planning)
guards       garde-fous (le cœur du contrôle)
preparation  manifeste + plan -> étapes
events       journal + traces pour Memory
index        ExecutionIndex · audit · report
engine       ExecutionEngine (façade)
cli          scc-brain-execution
```

## 5. Frontière de sûreté

Le `ExecutionEngine` **ne détient aucune API d'écriture** vers une autre couche : il
lit (décision/plan), **délègue** au Runtime, et n'écrit que dans son registre. Il ne
**mute jamais** le manifeste de la décision. Il **n'exécute rien** lui-même : le
Runtime est le seul exécutant (voir [`GOVERNANCE_SAFETY.md`](GOVERNANCE_SAFETY.md)).

## 6. Invariants tenus

| Invariant | Comment |
|-----------|---------|
| Aucun composant modifié | délégation/lecture via interfaces publiques seules |
| Aucune auto-modification | aucun accès en écriture hors du registre ; manifeste lu, jamais muté |
| Aucune exécution sans manifeste validé | garde-fou `decision_validated` |
| Aucune exécution si execution_status ≠ not_executed | garde-fou dédié |
| Aucune exécution automatique non autorisée | `execute` explicite + acteur autorisé |
| Fonctionne sans LLM | pilotage déterministe ; LLM optionnel (diagnostic) |
| Aucun réseau / dépendance externe | stdlib pur ; adaptateurs LLM non branchés |
| Déterminisme maximal | identifiants de contenu + horloge Runtime injectée |
| Traçabilité complète | événements, sources d'étapes, traces pour Memory |
