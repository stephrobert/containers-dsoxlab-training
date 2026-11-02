# Trois conteneurs en panne, trois causes différentes

Une chaîne de traitement tourne sur cette machine, en trois conteneurs :
`collecteur` ramasse, `expediteur` transmet, `scribe` consigne. Ce matin, les
trois sont en panne, et **les trois pannes sont indépendantes**.

**`collecteur` est sorti.** Il ne redémarre pas, et personne n'a lu son code de
sortie.

**`expediteur` redémarre sans fin.** On le voit repartir, encore et encore.

**`scribe` met dix secondes à s'arrêter**, et le rapport qu'il écrit est coupé
avant la fin.

Aucun de ces trois constats ne dit la cause. C'est à vous de les établir, et
elles ne sont pas les mêmes.

## Ce qui est attendu à la fin

1. `collecteur` **tourne**, à partir de l'image `lab-trois-pannes:1.0`.
2. `expediteur` **tourne**, il ne redémarre plus, et **sa politique de
   redémarrage est conservée** : elle n'est pas la panne.
3. `scribe` **tourne**, et il s'arrête proprement : un `docker stop` doit rendre
   la main en **moins de dix secondes**, avec un code de sortie **0 ou 143**, et
   le rapport doit être **complet**.
4. Le rapport complet, référence du passage comprise, est copié **sur
   l'hôte**, dans
   `/opt/lab-trois-pannes/diagnostic.txt`.
5. **Aucun conteneur de ce lab ne traîne à l'arrêt.**

Le rapport est écrit dans le conteneur, dans `/var/log/scribe.txt`. Il est
complet quand il porte **sa ligne de début et sa ligne de fin**.

Pour obtenir la copie : corrigez la panne du scribe, arrêtez-le proprement,
copiez son rapport, puis **relancez-le**. Le contrôle 5 exige qu'aucun conteneur
ne reste à l'arrêt.

L'énoncé complet est aussi sur la machine, dans
`/opt/lab-trois-pannes/MISSION.md`.

## Ce que vous n'avez pas à écrire

L'image `lab-trois-pannes:1.0` est fournie et porte les trois rôles : il n'y a
**rien à construire**. Elle lit la variable `ROLE`, et chaque rôle a ses propres
exigences. Ses journaux et ses codes de sortie les disent.

## Comment vous êtes noté

Cinq contrôles de poids égal, et **seul l'état final compte**. Aucune commande
n'est imposée.

Le seuil est de **75 sur 100**. Une exigence ne se compense par aucun total :
**un rapport perdu ou tronqué fait échouer l'épreuve**, même avec tout le reste
en place. Les deux premières pannes coûtent du temps ; celle-là coûte une
donnée, et une donnée perdue ne se rattrape pas.

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.
