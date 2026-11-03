# epreuve-fiabiliser-une-stack : l'épreuve du module de fiabilisation

## Ce que cette épreuve éprouve

Rendre fiable une stack qui marche déjà, ou presque. Elle clôt le module
« Fiabiliser une stack » et ne réexplique rien.

Son `lab_type: challenge` autorise son `exam_passing_score`, fixé à **75**. Les
cinq contrôles sont de poids égal, et l'un d'eux est critique.

## La stack livrée MARCHE, et c'est le point de départ

Personne ne laisse en production une stack qui ne démarre jamais. On laisse
celle qui démarre **quand on la relance deux fois**, et l'équipe prend
l'habitude de la relancer. C'est ce que cette épreuve reproduit, et c'est ce qui
la rend difficile : il n'y a pas de panne franche à trouver, il y a une
fragilité à nommer.

## Les cinq défauts, et pourquoi ils cohabitent dans un vrai fichier

| Défaut | Symptôme | Ce qu'il enseigne |
| --- | --- | --- |
| `depends_on` sans condition de santé | « il faut relancer deux fois » | démarrer un conteneur n'est pas rendre un service disponible |
| le mot de passe dans `environment` | aucun : tout marche | un secret lisible suit la stack partout, et personne ne le remarque |
| aucune limite mémoire | aucun, jusqu'au jour où | un service qui fuit emporte son voisin, pas lui-même |
| aucune politique de redémarrage | aucun, jusqu'à la première mort | un service qui meurt à quatre heures du matin reste mort jusqu'à ce que quelqu'un s'en aperçoive |
| le montage du source resté en déploiement | aucun, jusqu'au prochain déploiement | ce qui aide en développement nuit en production |

**Quatre des cinq n'ont aucun symptôme.** C'est la vraie leçon du module : la
fiabilité ne se mesure pas à ce qui tombe aujourd'hui.

## Pourquoi le contrôle du démarrage redémarre la stack lui-même

Un démarrage à froid ne se mesure qu'à froid. Une stack déjà debout a oublié
comment elle s'est levée, et la seconde tentative réussit toujours : c'est
précisément le symptôme qu'on vient corriger. Le contrôle fait donc `down` puis
`up -d`, et l'énoncé l'annonce.

Il exige **deux faits ensemble** : l'API répond, et aucun service n'a eu besoin
de redémarrer. Le second est le vrai contrôle. Avec une politique de redémarrage
et sans attente de la santé du coffre, l'API finit par répondre, après deux ou
trois morts : elle marche, et elle est fausse. Un barème qui ne regarderait que
la réponse validerait cette stack-là.

## L'exigence critique, et la fausse correction qu'elle attrape

**Le mot de passe lisible dans l'environnement fait échouer l'épreuve**, même à
80 points. Une variable d'environnement se lit par `docker inspect`, par
`docker compose config`, dans les journaux de celui qui a lancé la commande, et
dans le fichier versionné.

Mais le contrôle a **deux faces**, et c'est ce qui fait sa valeur : le secret
doit avoir disparu de ces endroits **et** être arrivé au service. Retirer une
variable sans la remplacer donne une stack propre et fausse, qui sert une valeur
par défaut ou rien du tout. Le contrôle compare donc la valeur servie au dérivé
que le lab a calculé du vrai mot de passe : elle ne peut être juste que si le
secret est bien arrivé.

## Pourquoi la limite est lue à deux endroits

`HostConfig.Memory` dit ce que le moteur a **retenu** de la déclaration.
`memory.max` du cgroup dit ce que le noyau **applique**. Lire les deux n'est pas
une précaution de style : ce sont deux faits distincts, et seul le second protège
l'hôte.

Neuf formes mesurées le 2026-11-02 sur Docker 29.9.2 et Compose 5.6.1, et le
résultat va contre l'intuition. `mem_limit` au niveau du service **et**
`deploy.resources.limits.memory` donnent tous **deux** `HostConfig.Memory` à
67108864 pour 64M : la forme n'est pas le piège. Une clé écrite au mauvais
niveau n'en est pas un non plus, car Compose valide son schéma et **refuse** le
fichier, avec un message et un code d'erreur.

Le seul cas accepté sans un mot et jamais appliqué est ailleurs :
`deploy.resources.reservations.memory` est une **réservation**, pas une limite.
Elle passe la validation, et elle laisse `HostConfig.Memory` à zéro et
`memory.max` à `max`. Le fichier parle de mémoire, et le conteneur n'a aucune
limite.

## Pourquoi le contrôle provoque une panne au lieu de tuer

Déclarer `restart:` et le relire dans l'inspection ne prouve rien : la valeur
peut être présente et ne jamais s'appliquer, par exemple sur un conteneur créé
avant le changement. La seule question qui compte est « revient-il ? ».

Elle ne se répond **pas** en tuant, et c'est ce que la leçon « Encadrer
ressources et redémarrage » enseigne. Mesuré le 2026-11-02 : après un
`docker kill` sur un conteneur en `restart: unless-stopped`, le moteur traite
l'arrêt comme **voulu**, le conteneur reste `exited` et le compteur de
redémarrages est encore à zéro vingt secondes plus tard. Un
`docker exec kill -9 1` ne fait rien non plus, le noyau protégeant le PID 1 d'un
namespace contre les signaux venus de ce namespace, SIGKILL compris.

Ce qu'une politique couvre vraiment est un processus qui **meurt de lui-même**.
Le contrôle pose donc le déclencheur de panne que le scénario annonce,
`/tmp/panne-provoquee`, et le service sort en erreur à la requête suivante.

## Pourquoi les contrôles sont indépendants

Deux d'entre eux se contrediraient sans cela : celui du démarrage à froid exige
un compteur de redémarrages à zéro, et celui de la politique **tue** un
conteneur pour vérifier qu'il repart. Le premier redémarre donc la stack
lui-même, et les deux ordres d'exécution rendent le même verdict.

C'est une leçon payée ailleurs dans ce catalogue : l'ordre d'exécution ne fait
pas partie du contrat de pytest, et un test qui dépend de la trace d'un autre
rend un verdict qui dépend du hasard.

## Ce que l'épreuve ne mesure pas

La sauvegarde, la restauration, le second hôte : c'est le sujet de
`epreuve-restaurer-une-stack`. Ici, un seul hôte et cinq points de fiabilité.
