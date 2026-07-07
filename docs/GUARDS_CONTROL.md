# Garde-fous & contrôle d'exécution

> Les garde-fous sont **le cœur** de cette couche : rien ne s'exécute qui ne les
> franchisse tous. Ils sont vérifiés à la préparation, et re-vérifiés à l'exécution.

## 1. Les six garde-fous

| Garde-fou | Condition |
|-----------|-----------|
| `manifest_present` | un manifeste décisionnel existe |
| `decision_validated` | la décision est **validated** (ni proposed, ni rejected, ni revoked) |
| `execution_status_not_executed` | `execution_status == "not_executed"` |
| `not_sovereign` | le manifeste n'est **pas** marqué souverain |
| `human_validation_present` | si le manifeste requiert une validation humaine, un **approbateur** existe |
| `actor_authorized` | l'acteur déclencheur est **autorisé** |

Si **un seul** échoue → l'exécution est **refusée** (statut `refused`), **aucune
étape n'est lancée**.

## 2. Autorisation

Un acteur est autorisé s'il figure dans `authorized_actors` (configuration) **ou**
s'il est l'**approbateur** de la décision. L'exécution (`execute`) exige un acteur
autorisé : **aucune exécution automatique** — elle est toujours déclenchée
explicitement.

## 3. Contrôle en deux temps

```
prepare()  -> garde-fous -> PREPARED (étapes prêtes) | REFUSED (interdit)
execute()  -> [acteur autorisé] -> re-vérifie garde-fous -> délègue au Runtime
```

- Une exécution `refused` **ne peut jamais** passer à `running` (transition interdite).
- Une exécution ne peut être lancée **qu'une fois** (depuis `prepared`).
- À l'exécution, les garde-fous sont **re-vérifiés** ; un acteur non autorisé est
  rejeté (`GuardRejected`).

## 4. Cycle de vie

```
prepared ──▶ running ──▶ succeeded | failed
   │           │
   │           └──▶ cancelled | revoked
   ├──▶ cancelled | revoked
   └──▶ (refused : terminal, aucune exécution)
succeeded ──▶ revoked
```

`cancel` et `revoke` exigent aussi un **acteur autorisé** et sont **tracés**.

## 5. Délégation au Runtime

Chaque étape devient un **job Runtime** soumis via l'interface publique. La
**gouvernance du Runtime** s'applique : une action de type T3 (sensitive_action) est
**bloquée puis validée humainement** au niveau du Runtime avant de s'exécuter (action
simulée dans le socle). Execution n'exécute rien lui-même.

## 6. Audit

`audit()` vérifie que :
- toute exécution ayant **tourné** (`running`/`succeeded`/`failed`) avait des
  **garde-fous OK** et une **décision validée** ;
- une exécution **refusée** n'a lancé **aucune** étape ;
- l'intégrité et la traçabilité des étapes sont respectées.
