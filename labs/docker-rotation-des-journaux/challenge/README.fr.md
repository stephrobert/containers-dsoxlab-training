# Contrat fonctionnel : docker-rotation-des-journaux

Travaillez sur `docker.lab`. Le service `dsoxlab-log-rotation` doit rester actif
et conserver son label `dsoxlab.lab`.

Trois contrôles indépendants mesurent trois choses différentes, et le premier ne
suffit pas.

## 1. Le pilote déclaré borne les journaux

Le service utilise le pilote `json-file`, avec `max-size=1k` et `max-file=3`.

C'est ce qui a été **demandé au démon**, et c'est la seule chose que mesurait la
version précédente de ce lab. Un plafond accepté par le démon et jamais appliqué
l'aurait satisfaite, et vous auriez eu le point sans que votre journal soit
borné.

## 2. Les lignes les plus anciennes ont été jetées

Le service émet cent lignes numérotées de 0 à 99, puis dort. Si la rotation
mord, la première n'est plus lisible et la centième l'est encore.

C'est observable par `docker logs` seul, sans aucun privilège, et c'est mesuré :

| Réglage | Lignes retenues | Première ligne |
| --- | --- | --- |
| `max-size=20m max-file=5` | 100 | `0` |
| `max-size=1k max-file=3` | 16 | `84` |

Le contrôle exige aussi que la **centième** ligne soit présente : une rotation
qui jetterait les lignes récentes au lieu des anciennes ne rendrait pas le
service consultable.

## 3. Le volume retenu tient dans le budget déclaré

Le contenu retenu ne dépasse pas ce que trois fichiers de 1 Kio peuvent
conserver.

Ce n'est pas une redite du contrôle 2. Jeter les lignes anciennes montre que la
rotation tourne ; tenir dans le budget montre qu'elle tourne avec les **bonnes
valeurs**. Une rotation réglée sur 1 Mio jetterait aussi, beaucoup plus tard, et
le contrôle 2 seul l'accepterait.

Le relevé ne touche pas `/var/lib/docker`, et c'est délibéré : lire les fichiers
de journal demande root, ce qui rendrait la vérification dépendante d'un détail
d'environnement. Le contenu rendu par `docker logs` est de toute façon plus petit
que les fichiers JSON qui l'encapsulent : s'il dépasse le budget, les fichiers le
dépassent aussi.

## Ce qui n'est pas noté, et pourquoi on vous le dit

Deux vérifications précèdent les mesures sans être des exigences : que le service
existe et porte son label, et que ses journaux soient lisibles. Sans elles aucun
contrôle ne peut observer quoi que ce soit, et un contrôle qui n'a pas pu
regarder ne doit jamais conclure au vert. Quand la lecture échoue sur un service
qui tourne, le message vous dit que ce n'est pas votre faute.

Une limite de ce contrat, pour que personne ne s'y trompe : les contrôles 2 et 3
mordent réellement, mais ils ne refusent **jamais seuls**, puisque toute erreur
sur les bornes est aussi vue par le contrôle 1. Ils existent parce qu'ils ne
mesurent pas la même chose que lui : il croit la déclaration, eux regardent le
journal. Le jour où le moteur accepterait une option sans l'appliquer, ils
seraient les seuls à le voir.
