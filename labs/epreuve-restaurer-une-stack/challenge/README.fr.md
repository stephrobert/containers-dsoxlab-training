# Scénario

Un client appelle : le service ne répond plus. Vous ouvrez la console de l'hôte
qui le portait, et ce que vous voyez ne ressemble à rien de ce que vous attendiez.

La décision est prise avant que vous ayez fini de regarder : cet hôte n'est plus
de confiance, le service repart ailleurs. Vous avez l'autre machine, le fichier
de la pile, l'image, et une sauvegarde prise avant la panne.

Vous avez aussi une consigne que personne ne répétera : la base de données
n'était joignable que par l'API, et elle doit le rester. C'est ce qui a été
écrit dans le dossier de sécurité, et c'est ce qui sera relu si l'incident monte.

## Mission

Établissez l'état réel, remontez le service sur l'autre hôte, restaurez
l'enregistrement témoin, et ne perdez pas l'isolement du réseau de données en
chemin.

C'est une **épreuve** : le seuil de réussite est de 75 %. Le détail de ce qui
est attendu est dans `/opt/lab-restauration/MISSION.md`, sur l'hôte où le
service doit repartir.

**Une exigence n'est compensée par aucun total : la donnée témoin doit être restaurée ET servie à travers le frontal.** Présente mais non servie ne compte pas : une donnée qu'on ne peut pas rendre n'est pas restaurée, elle est seulement là.

## Ce qui est demandé

Deux machines. `docker.lab` portait la pile ; elle **n'est plus de confiance**.
`docker-client.lab` est l'hôte sur lequel le service doit repartir.

Les deux portent déjà :

- `/opt/lab-restauration/compose.yaml`, la pile telle qu'elle tournait ;
- l'image `lab-restauration/service:1.0`, construite localement ;
- `/opt/lab-restauration/sauvegarde/`, la sauvegarde prise avant la panne.

**Pour travailler sur `docker-client.lab`, ouvrez-y une session depuis votre
poste :**

```bash
dsoxlab ssh docker-client
```

Le saut d'une machine du lab vers l'autre n'est **pas** possible : les deux hôtes
ne se font pas confiance, et c'est volontaire. On passe par son propre poste,
qui est le seul à parler aux deux.

La pile a trois étages. `front` est publié sur `127.0.0.1:18090` et ne voit que
`api` ; `api` voit les deux côtés ; `db` n'est que sur le réseau de données, qui
est **interne**. Une requête métier traverse les trois, et le service rend la
liste des étages traversés.

C'est une **épreuve** : le seuil de réussite est de 75 %.

### 1. Établir l'état réel

Rien ne vous dit ce qui a été détruit, et c'est volontaire. Commencez par le
mesurer plutôt que par le supposer : conteneurs, volumes, réseaux, et ce que la
sauvegarde contient.

### 2. Remonter le service sur `docker-client.lab`

Les trois étages doivent tourner, dans le projet Compose `dsoxlab-restauration`,
et la requête métier doit traverser `front`, `api` et `db` dans cet ordre.

### 3. Restaurer l'enregistrement témoin

Un enregistrement avait été écrit **à travers le front** avant la panne. Il doit
être servi de nouveau par la pile restaurée, et lu par le même chemin : une
donnée qu'on ne peut pas servir n'est pas restaurée, elle est seulement
présente.

La sauvegarde est dans `/opt/lab-restauration/sauvegarde/`.

### 4. Ne pas perdre l'isolement en chemin

Le réseau qui porte `db` doit rester **interne**, et `db` ne doit publier aucun
port.

Mettre la pile à plat, tout sur un réseau, est le raccourci qui fait « marcher »
une restauration. Il est refusé ici, et le contrôle ne lit pas votre fichier : il
mesure sur le moteur, en vérifiant qu'une sonde posée sur le réseau public
n'atteint pas `db`, et que `api` l'atteint.

### L'état final attendu

Sur `docker-client.lab` : les trois étages debout, la requête métier qui les
traverse, le témoin servi, le réseau de données interne et `db` sans port
publié.

### Ce qui n'est pas noté

La façon dont vous restaurez la donnée, ni l'ordre dans lequel vous remontez les
étages. Le contrôle lit l'état des deux machines.
