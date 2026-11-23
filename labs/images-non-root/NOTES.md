# images-non-root : `USER` change l'identité, et aucun droit

## Ce que ce lab éprouve

Que `USER` ne change **aucun droit** sur ce qui a déjà été déposé. Les
répertoires créés avant lui appartiennent à root, et l'application cesse
d'écrire au moment même où elle cesse d'être privilégiée.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30, la même application sous trois écritures :

| Écriture | uid | Écriture dans /donnees |
| --- | --- | --- |
| sans `USER` | 0 | ok |
| `USER` seul | 10001 | **refusée**, « Permission denied » |
| `USER` + propriétaire aligné | 10001 | ok |

Et les deux fausses réponses ont été **éprouvées** : `USER appli` au lieu de
l'uid numérique rend **3/4**, et `chmod 777` au lieu du `chown` rend **3/4**
aussi. Chacune n'est refusée que par le contrôle qui porte sur elle.

## Deux mesures qui ont décidé de ce que le lab ne note pas

**`docker run --user 0:0` sur l'image non-root rend uid=0.** Le `USER` du
Dockerfile est donc une valeur par défaut, pas une garantie. C'est pourquoi les
contrôles lancent l'image **sans aucune option d'identité** : avec l'option,
n'importe quelle image passerait, et le lab noterait la commande au lieu de
l'image.

**Un non-root écoute sur le port 80** dans un conteneur, mesuré. On lit souvent
qu'il faut être root sous 1024 ; le moteur accorde la capacité correspondante
par défaut. Aucun contrôle ne porte donc sur les ports : **ce serait mesurer une
croyance**, et un lab qui note une croyance l'enseigne.

## Pourquoi le moyen est noté, et pas seulement l'effet

Deux réponses font écrire l'application : lui donner le répertoire, ou l'ouvrir
à tout le monde. La seconde marche parfaitement, et elle est refusée.

Rendre un répertoire inscriptible par n'importe qui pour qu'un processus non
privilégié y écrive défait exactement ce que le passage en non-root cherchait.
Le deuxième contrôle mesure donc l'effet, et le troisième le moyen.

C'est la même structure que `troubleshoot-permission-refusee`, et pour la même
raison : un lab de sécurité qui accepte le raccourci enseigne le raccourci.

## Pourquoi l'uid numérique est exigé

Un `USER appli` se résout dans le `/etc/passwd` de l'image. Un orchestrateur
qui refuse les conteneurs root ne lit pas ce fichier : il lit la déclaration, et
il ne peut pas prouver qu'un nom n'est pas root.

Ce point n'a **pas** été mesuré ici, faute d'orchestrateur sur la machine du
lab : c'est la raison de la règle, pas une mesure. Ce qui est mesuré, c'est que
`USER appli` donne `.Config.User = 'appli'` et que `USER 10001:10001` donne
`'10001:10001'` : la déclaration est bien ce que l'image transmet.

## Un défaut de lecture, attrapé par le cycle

Le troisième contrôle refusait la solution de référence en annonçant un uid
impossible, « 10001 gid=10001 ». L'extracteur découpait chaque ligne sur son
premier `=`, et la ligne `uid=10001 gid=10001` en porte deux. Le découpage se
fait désormais par mots.

Le défaut est instructif : le contrôle **mesurait juste et lisait faux**, et son
message accusait l'apprenant d'un écart qui n'existait pas.

## L'état de départ est cassé, et c'est la règle du dépôt

Le setup ne construit pas l'image : les quatre contrôles sont faux avant tout
travail. Une tâche vérifie que le socle existe, que l'image de l'apprenant
n'existe pas, et que le Dockerfile de départ ne porte **aucun** `USER`.

## Ce que le lab n'exige pas

Un uid précis, ni un nom d'utilisateur, ni un mode exact. Seuls comptent un uid
non nul, un répertoire qui appartient à l'application, un mode qui n'ouvre pas
l'écriture à tous, et une déclaration numérique. Le jeton est tiré par le setup :
rien n'est écrit en dur dans les contrôles.
