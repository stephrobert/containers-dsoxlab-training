# La base tombe, et sa limite mémoire semblait large

## La situation

Une base de données tourne en conteneur, avec une limite mémoire de 512 Mo. Elle
en consomme 300 en régime établi, ce qui laisse de la marge.

Elle est tuée par le noyau une fois par semaine, à chaque gros rapport. Les
métriques de l'application montrent 300 Mo au moment de la mort. Celles du
conteneur montrent 512.

L'écart est dans la **mémoire partagée**. La base s'en sert pour ses tampons de
tri, elle y écrit plusieurs centaines de mégaoctets pendant le rapport, et cette
mémoire-là est comptée dans celle du conteneur. L'application n'en sait rien :
pour elle, `/dev/shm` est un système de fichiers, pas de la mémoire.

Au même moment, un autre service refuse des connexions en se plaignant de
descripteurs de fichiers, sur une machine qui n'en manque pas du tout.

## L'objectif

Mesurer ces deux réglages qu'on ne regarde jamais, puis les poser. **Aucun
conteneur ne tourne** : vous les lancez vous-même, parce que les deux ne se
posent qu'à la création.

L'image `lab-ulimits:1.0` est prête.

Renseignez les deux lignes de `/opt/lab-ulimits/reponses.txt`, en lançant un
conteneur **sans aucune option** et en l'interrogeant :

```text
shm_defaut_mo=<la taille de /dev/shm par défaut, EN MÉGAOCTETS, sans unité>
nofile_defaut=<la limite de descripteurs de fichiers par défaut, telle que le
               conteneur la déclare>
```

La deuxième réponse **surprend par sa taille**. Ce n'est pas une erreur de
lecture.

Puis lancez un conteneur nommé `etroit` avec **deux** réglages :

```text
/dev/shm de 256 Mo, et une limite de 1024 descripteurs de fichiers
```

Enfin, écrivez **128 Mo** dans son `/dev/shm`, et constatez ce que cela fait à
la **mémoire de son cgroup**.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Deux mécanismes qui ne sont pas de la même famille

Les cgroups plafonnent **depuis l'extérieur** : le noyau compte et refuse. Les
ulimits sont un mécanisme POSIX, bien antérieur, que **le processus porte
lui-même**.

Les chercher au même endroit est l'erreur que ce lab lève : la taille de la
mémoire partagée se lit dans l'inspection du conteneur et dans son système de
fichiers, la limite de descripteurs **seulement** depuis l'intérieur.

## La leçon du quatrième contrôle

`/dev/shm` est un **tmpfs**, donc de la mémoire, et cette mémoire est comptée
dans le cgroup du conteneur.

Une limite mémoire doit donc tenir compte de la taille de `/dev/shm`, sans quoi
le conteneur se fait tuer pour une mémoire qu'il croyait « à part ». C'est
l'incident du scénario, et c'est une cause de mort qui ne se lit dans aucune
documentation d'application.

## Ce qui est noté

L'**état du système**. Les deux valeurs par défaut sont **remesurées** au moment
de la notation, sur un conteneur neuf : le jour où Docker changera ses défauts,
ces contrôles suivront au lieu de devenir faux.

Et la quatrième mesure est une **pesée** : l'occupation de `/dev/shm` d'un côté,
la mémoire du cgroup de l'autre, et la comparaison des deux.
