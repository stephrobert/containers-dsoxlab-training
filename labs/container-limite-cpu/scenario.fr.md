# L'application est lente, et elle a pourtant de la marge

## La situation

Un service tourne en conteneur, bridé à la moitié d'un processeur, ce qui est
largement suffisant pour ce qu'il fait. Et il est lent. Pas en panne : lent,
par à-coups, avec des temps de réponse qui triplent sans raison apparente.

Les métriques de la machine sont calmes. Celles du conteneur montrent qu'il
consomme exactement ce qu'on lui a accordé, ce qui devrait rassurer.

La cause est dans l'application elle-même, et elle est banale : au démarrage,
elle demande au système combien de processeurs sont disponibles, et dimensionne
ses fils d'exécution sur cette réponse. Elle en a obtenu le nombre de la
**machine**, pas celui de sa limite. Elle lance donc deux fois trop de travail
en parallèle, et passe son temps à se faire retenir par le noyau.

## L'objectif

Voir d'où vient le malentendu. Le conteneur `brideur` tourne, bridé à 0.5 CPU,
et il ne fait rien pour l'instant.

Renseignez les deux lignes de `/opt/lab-cpu/reponses.txt` :

```text
quota=<ce que le cgroup de `brideur` déclare comme limite de temps processeur,
       TEL QUEL>
cpu_vus=<le nombre de CPU que `brideur` VOIT, de l'intérieur>
```

La deuxième réponse est celle qui compte, et elle surprend. **Comparez-la au
nombre de CPU de la machine avant de conclure que vous vous êtes trompé.**

Puis deux gestes :

1. lancez un conteneur nommé `epingle` qui, lui, ne voit **qu'un seul** CPU. Ce
   n'est pas la même option, et ce n'est pas le même mécanisme.
2. mettez `brideur` sous charge, assez pour que le noyau doive l'**étrangler**.
   Son cgroup compte les étranglements : tant que le compteur est à zéro, la
   limite n'a jamais mordu.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Deux mécanismes qu'on confond

| Ce qu'on pose | Ce que le noyau limite | Ce que le conteneur voit |
| --- | --- | --- |
| une part de CPU | le **temps** accordé par tranche | **tout**, inchangé |
| un ensemble de CPU | les **processeurs** utilisables | moins |

Le premier est celui qu'on emploie partout, et c'est lui qui crée le
malentendu. Le second est plus rare, et c'est le seul qui change la réponse que
le système donne à l'application.

## Ce qui est noté

L'**état du système**, et le quatrième contrôle demande une **preuve** plutôt
qu'une déclaration. Une limite qu'on n'a jamais vue mordre est une limite qu'on
croit sur parole : elle est peut-être juste, elle n'est pas prouvée.

C'est la différence entre lire une configuration et constater un comportement,
et c'est la seule qui compte le jour où une application est lente sans qu'on
sache pourquoi.
