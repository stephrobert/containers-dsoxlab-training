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

## Les quatre défauts, et pourquoi ils cohabitent dans un vrai fichier

| Défaut | Symptôme | Ce qu'il enseigne |
| --- | --- | --- |
| `depends_on` sans condition de santé | « il faut relancer deux fois » | démarrer un conteneur n'est pas rendre un service disponible |
| le mot de passe dans `environment` | aucun : tout marche | un secret lisible suit la stack partout, et personne ne le remarque |
| aucune limite mémoire | aucun, jusqu'au jour où | un service qui fuit emporte son voisin, pas lui-même |
| le montage du source resté en déploiement | aucun, jusqu'au prochain déploiement | ce qui aide en développement nuit en production |

**Trois des quatre n'ont aucun symptôme.** C'est la vraie leçon du module : la
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
`memory.max` du cgroup dit ce que le noyau **applique**. Les deux peuvent
différer, et le cas est courant : une limite écrite dans une section de
déploiement destinée à un orchestrateur absent est lue par Compose, acceptée
sans erreur, et jamais appliquée. Le conteneur reste sans limite, et le fichier
a l'air juste.

## Pourquoi le contrôle de la politique tue un conteneur

Déclarer `restart:` et le relire dans l'inspection ne prouve rien : la valeur
peut être présente et ne jamais s'appliquer, par exemple sur un conteneur créé
avant le changement. La seule question qui compte est « revient-il ? », et elle
se répond en tuant.

`docker kill` et non `docker stop` : un arrêt demandé est un arrêt voulu, et
aucune politique ne redémarre un conteneur qu'on a arrêté soi-même. Confondre
les deux fait conclure à tort que la politique ne marche pas.

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
`epreuve-restaurer-une-stack`. Ici, un seul hôte et quatre points de fiabilité.
