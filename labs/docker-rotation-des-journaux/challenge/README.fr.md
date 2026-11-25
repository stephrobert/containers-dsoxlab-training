# Un service bavard remplit le disque

## La situation

Sur `docker.lab`, le service `dsoxlab-log-rotation` écrit un flux limité, mais
son journal a le droit de devenir beaucoup trop gros. Seul ce service est
concerné : les valeurs par défaut du démon ne doivent pas changer.

## Mission

Le service garde ses journaux `json-file` dans des fichiers de 1 Kio au plus,
trois fichiers conservés. Il doit rester actif et garder son label `dsoxlab.lab`.
L'énoncé est aussi déposé dans `/opt/dsoxlab-docker-rotation-des-journaux/MISSION.md`.

## Ce qui est noté

### 1. Le pilote déclaré borne les journaux

Le service utilise le pilote `json-file`, avec `max-size=1k` et `max-file=3`.

C'est ce qui a été **demandé au démon**. Les deux contrôles suivants mesurent ce
qu'il en fait.

### 2. Les lignes les plus anciennes ont été jetées

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

### 3. Le volume retenu tient dans le budget déclaré

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
