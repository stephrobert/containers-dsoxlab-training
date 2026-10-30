# docker-cycle-de-vie : redémarrer n'est pas recréer

## Ce que ce lab éprouve

Que les états d'un conteneur forment un **graphe**, et qu'on s'y déplace sans
repartir de zéro. Le lab précédent enseignait trois verbes ; celui-ci enseigne
qu'un conteneur arrêté se redémarre, garde son identité, et garde ce qu'on a
écrit dedans.

## Le contrôle qui porte tout le lab

Comparer l'identifiant de `dormeur` à celui que le setup a relevé **avant** tout
travail. C'est le seul moyen de distinguer « j'ai redémarré le conteneur » de
« j'en ai lancé un autre du même nom » : les deux donnent un conteneur qui
tourne, et un seul est le geste enseigné.

Ici le **chemin est la compétence**, donc il se mesure. Mais il se mesure par
son empreinte, jamais en regardant les commandes tapées : `docker start`,
`docker restart` ou un démarrage par l'API aboutissent au même état avec le
même identifiant, et tous les trois comptent.

L'empreinte est laissée **lisible** par l'apprenant dans
`/opt/lab-cycle/id-dormeur.txt`. Un contrôle qu'on peut vérifier soi-même
enseigne ; un contrôle opaque fait deviner.

## Pourquoi le fichier n'est pas une redite

Un conteneur recréé est vierge. Le contrôle qui lit `/empreinte.txt` mesure donc
la **conséquence observable** de la faute que le contrôle précédent détecte.

C'est ce qui rend la leçon tenable sans qu'on l'affirme : l'apprenant qui a
recréé voit ses données disparaître, ce qui est exactement l'incident que le
scénario raconte.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `dormeur` | `exited`, avec `/empreinte.txt` | le redémarrer | 1 et 2 |
| `actif` | `running` | le mettre en pause | 3 |
| *rien* | absent | faire sortir `sortie` en 42 | 4 |

Une tâche du setup **vérifie** cet état avant de rendre la main : `dormeur
exited`, `actif running`, aucun `sortie`. Sans elle, un passage mal nettoyé
rendrait le lab déjà résolu avant d'être posé.

## Un piège du cleanup, payé d'avance

`docker rm` **refuse** un conteneur en pause, et c'est précisément l'état que ce
lab demande de produire. Le `clean` échouerait donc sur le lab dont la pause est
le sujet, avec un message parlant d'un refus sans dire pourquoi. D'où le `-f`,
et d'où ce commentaire dans le `cleanup.yaml`.

## Ce que le lab n'exige pas

Un ordre. Les quatre gestes sont indépendants, et le contrôle 2 est le seul à
dépendre d'un autre, par construction et non par exigence : il lit un fichier
dans un conteneur qui doit tourner.
