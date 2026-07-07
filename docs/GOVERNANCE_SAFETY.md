# Gouvernance & sûreté de l'exécution

> **Principes cardinaux : aucune exécution sans manifeste validé ; aucune exécution
> automatique non autorisée ; aucune auto-modification ; traçabilité complète.**

## 1. Aucune exécution sans manifeste validé

L'exécution est **interdite** si la décision n'est pas `validated`, ou si
`execution_status != not_executed`, ou si le manifeste est `sovereign`, ou si la
validation humaine requise est absente. Ces garde-fous sont vérifiés à la préparation
**et** re-vérifiés à l'exécution (voir [`GUARDS_CONTROL.md`](GUARDS_CONTROL.md)).

## 2. Aucune exécution automatique

L'exécution (`execute`) est **toujours déclenchée explicitement** par un **acteur
autorisé**. Il n'existe aucun chemin d'exécution automatique : la préparation crée un
run *préparé* qui attend un déclenchement humain/autorisé.

## 3. Aucune auto-modification

Le `ExecutionEngine` **n'importe aucune API d'écriture** d'une autre couche. Il **lit**
la décision et le plan, **délègue** au Runtime (qui gouverne ses propres jobs), et
n'écrit que dans son registre (`data/executions.jsonl`). Il **ne mute jamais** le
manifeste de la décision. Il est donc **structurellement incapable** de modifier
Decision, Planning, Runtime, Memory, le graphe, une doctrine ou du code.

## 4. Le Runtime reste l'exécutant technique

Execution ne réalise **aucune** action technique : elle **délègue** au Runtime, seul
exécutant. La gouvernance du Runtime (garde-fou humain T3, vetos) s'applique
intégralement aux jobs délégués.

## 5. Traçabilité complète

Chaque exécution journalise ses **événements** (append-only), trace chaque étape vers
sa **source** et vers son **job Runtime**, et produit des **traces neutres pour
Memory** — sans jamais écrire dans Memory.

## 6. Audit

`audit()` vérifie intégrité (empreintes d'étapes), traçabilité (sources), et sûreté
(exécution seulement si garde-fous OK et décision validée ; refus sans étape lancée).

## 7. Alignement doctrinal

- **Traçabilité complète** ([[SCC-DOC-0016]]) : événements, sources, traces.
- **Gouvernance avant extension** ([[SCC-DOC-0015]]) : rien ne s'exécute sans manifeste
  validé et autorisation.
- **Lecture seule / append-only** ([[SCC-DOC-0006]], [[SCC-DOC-0007]]) : registre
  append-only ; décision lue, jamais mutée.
- **Garde-fou humain T3** : conservé au niveau du Runtime pour les actions critiques.
- **Intelligence lourde optionnelle et branchable** ([[SCC-DOC-0029]]) : un LLM peut
  aider au diagnostic/rapport, jamais déclencher ni modifier une exécution.
