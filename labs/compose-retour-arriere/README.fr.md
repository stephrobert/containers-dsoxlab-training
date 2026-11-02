# compose-retour-arriere

**Public :** l'apprenant.

Un retour en arrière ramène le code, pas les données, et une migration de
schéma le ferme définitivement. Ce lab fait mesurer les deux.

## Ce que vous saurez faire

- Déployer une release **par son digest** plutôt que par une étiquette, et dire
  ce que cela change.
- Revenir à la release précédente sans perdre ce qui a été écrit entre-temps.
- Reconnaître une migration irréversible, et établir à partir de quel moment le
  retour en arrière n'est plus une option.
- Lire le refus d'une release qui ne sait pas lire l'état, et en tirer la bonne
  conclusion : elle protège les données au lieu de les abîmer.

## Comment c'est noté

Quatre contrôles de poids égal, tous sur l'**état final** :

1. la `3.0` tourne, et elle est désignée par un digest, pas par une étiquette ;
2. l'état est en schéma 2, et les enregistrements y sont sous leur forme migrée ;
3. les **deux** enregistrements ont survécu, celui d'avant votre arrivée comme
   le vôtre ;
4. le retour à la `2.0` est refusé, ce que le contrôle **mesure lui-même**, et
   votre constat nomme les trois valeurs que la machine donne.

Le chemin suivi n'est pas noté : seul l'état compte.

## Ce que le lab ne fait pas

Il ne vous demande pas de réparer la situation. Une migration irréversible ne se
répare pas après coup : elle se **sait avant**, et c'est pour cela que ce lab
existe.
