# Modèle d'exécution

## 1. La demande (`ExecutionRequest`)

```json
{
  "id": "exreq_…", "decision_id": "dec_…",
  "manifest": { "...": "manifeste décisionnel (lu depuis Decision 15)" },
  "decision_status": "validated", "actor": "frederique"
}
```

La demande référence une **décision** (dont le manifeste et le statut sont récupérés
via l'interface publique de Decision), ou fournit un **manifeste + statut** directs
(mode hermétique).

## 2. L'étape (`ExecutionStep`)

```json
{
  "id": "step_…", "order": 1, "name": "Publier en beta privée",
  "kind": "echo", "params": {"action": "…"}, "status": "succeeded",
  "job_id": "job_000000000001", "sources": ["decision_manifest:opt_…"], "hash": "…"
}
```

Chaque étape est **matérialisée comme un job Runtime** (type hermétique par défaut)
et **tracée** vers sa source (manifeste, plan).

## 3. L'exécution (`ExecutionRun`)

```
{ request, decision_id, subject, guards{ok, checks, refusals, authorized_actors},
  steps[], status, events[], report{}, traces_for_memory[], authorization{actor, approver} }
```

- **guards** : le résultat des garde-fous (voir [`GUARDS_CONTROL.md`](GUARDS_CONTROL.md)).
- **status** : `prepared` | `refused` → `running` → `succeeded` | `failed` ;
  `prepared`/`running` → `cancelled` ; (…) → `revoked`.
- **events** : journal append-only (prepared, running, step_*, succeeded/failed…).
- **report** : synthèse (statuts d'étapes, garde-fous, événements).
- **traces_for_memory** : traces neutres prêtes pour une future ingestion par Memory.

## 4. Traçabilité (aval → amont)

```
Exécution ──▶ Étapes ──▶ jobs Runtime (job_id)      (délégation technique)
   │             └──▶ sources (decision_manifest:… / plan:…)
   └──▶ decision_id + guards (statut de décision, autorisations)
```

## 5. Traces pour Memory (plus tard)

Chaque événement est exporté en trace neutre
`{kind: "event", subtype: "execution.<type>", actor, timestamp, data}`. Execution
**n'écrit pas** dans Memory ; elle produit un format qu'une future intégration pourra
ingérer.

## 6. Déterminisme

Identifiants dérivés du **contenu** ; Runtime piloté avec `FixedClock` +
`SequentialFactory` ; horodatage figé (`as_of`). Préparer et exécuter deux fois la
même demande produit la **même** exécution (vérifié en processus et cross-process).
