# epreuve-restaurer-une-stack

**Public :** l'apprenant.

Une restauration ne se juge pas sur « le service répond ». Elle se juge sur la
donnée retrouvée **et** sur ce qui n'a pas été perdu en chemin. Cette épreuve
mesure les deux.

## Ce que vous saurez faire

- Établir l'état réel d'une pile tombée, sans vous fier à ce qu'on vous en dit.
- Remonter trois étages sur un autre hôte, et vérifier que la requête métier les
  traverse vraiment.
- Restaurer une donnée et la faire **servir** par le chemin métier, pas
  seulement la remettre sur un disque.
- Garder un réseau de données interne pendant une restauration, et prouver
  l'isolement par la mesure plutôt que par la lecture du fichier.

## Comment c'est noté

Quatre contrôles de poids égal, seuil de réussite **75 %** :

1. les trois étages tournent sur le client, et la requête métier traverse
   `front`, `api` puis `db` ;
2. l'enregistrement témoin est servi de nouveau, par le même chemin ;
3. le réseau de `db` est interne et `db` ne publie aucun port, lu **sur le
   moteur** ;
4. une sonde posée sur le réseau public n'atteint pas `db`, et `api` l'atteint.

Le quatrième contrôle regarde les deux sens, et il faut les deux : sans le
second, une pile dont `db` serait simplement arrêté passerait le premier.

## Ce que l'épreuve ne fait pas

Elle ne vous dit pas ce qui a été détruit. L'établir fait partie du travail, et
c'est ce qui sépare une restauration d'une reconstruction à l'aveugle.
