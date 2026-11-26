# Lire qui appelle qui

La leçon lance un même `sleep` avec Podman, containerd et Docker, et lit
l'arbre des processus : un moniteur par conteneur, conmon chez Podman, un shim
chez containerd, et le runtime au bout. Elle redémarre containerd pour montrer
que le conteneur survit. Ce cours vous fait voir ce qu'elle ne montre pas.
D'abord, à quoi sert conmon une fois le conteneur terminé, et pourquoi un
processus porte deux numéros. Ensuite, la différence entre un conteneur et
une tâche containerd, et des images qui ne passent pas d'un namespace à
l'autre. Enfin, ce qui arrive quand le shim disparaît.

Vous travaillez sur Alpine 3.23, avec des conteneurs nommés `essai-*` et les
namespaces containerd `essai` et `essai2`. Le challenge porte sur une autre
image et d'autres noms : vous le ferez seul, à la fin.

Page associée : [Runtime, moteur, orchestrateur : qui fait quoi ?](https://www.stephane-robert.info/docs/conteneurisation/runtime-moteur-orchestrateur/).

## Avant de commencer

Lancez le lab :

```bash
dsoxlab run runtime-qui-appelle-qui
```

Vous êtes maintenant connecté à `oci.lab`, une Debian 13 sans Docker. Podman
et containerd s'emploient en root : passez root pour tout le cours, comme dans
la leçon. Puis tirez l'image du cours avec Podman, par son digest :

```bash
sudo -i
podman --version
ctr --version
A=docker.io/library/alpine@sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2
podman pull -q "$A"
```

```text
podman version 5.4.2
ctr github.com/containerd/containerd 1.7.24~ds1
164b5c6a230f645862b6123e07cf0a67f2f03371696aa82a12ccf3589e87c016
```

Les sorties de ce cours ont été relevées sur cette machine le 26 novembre
2026, avec Podman 5.4.2 et containerd 1.7.24, les versions des paquets de
Debian 13. Les PID et les identifiants changent d'un lancement à l'autre.
**Gardez le même terminal jusqu'au nettoyage** : les variables des exercices
n'existent que dans lui.

## Exercice 1 : conmon garde le code de sortie

La leçon montre que Podman ne laisse aucun démon : c'est conmon qui reste près
du conteneur. Lancez un conteneur qui se termine au bout de trois secondes
avec le code 3, comptez les conmon qui le suivent, puis attendez sa fin :

```bash
podman run -d --name essai-code "$A" sh -c 'sleep 3; exit 3'
pgrep -a conmon | grep -c essai-code
sleep 5
podman inspect -f '{{.State.Status}} {{.State.ExitCode}}' essai-code
pgrep -a conmon | grep -c essai-code
podman rm essai-code
```

```text
e57382f918cf1eaee46da697a36824ae7b60ae02129ba5e5279175683f53aa60
1
exited 3
0
essai-code
```

Pendant que le conteneur tourne, un conmon le suit. Une fois le conteneur
fini, conmon est parti lui aussi, et pourtant Podman connaît le code de
sortie : `3`. Aucune commande `podman` ne tournait à ce moment-là. C'est
conmon qui a attendu la fin du processus et noté son code avant de partir.
Sans lui, personne ne l'aurait recueilli.

## Exercice 2 : un processus, deux numéros

Lancez un conteneur durable, puis lisez son numéro de processus vu de l'hôte
et vu du conteneur :

```bash
podman run -d --name essai-pid "$A" sleep infinity
P=$(podman inspect -f '{{.State.Pid}}' essai-pid)
grep NSpid /proc/$P/status
podman exec essai-pid ps -o pid,comm
podman rm -f -t 0 essai-pid
```

```text
3c5379d4e3d106f10594006f82e50fdc9ddb526c3b0b804c7d5d1a0e6add1547
NSpid:	122599	1
PID   COMMAND
    1 sleep
    2 ps
essai-pid
```

La ligne `NSpid` donne les deux numéros du même processus : `122599` dans le
namespace `pid` de l'hôte, `1` dans celui du conteneur. Quand vous cherchez le
parent d'un conteneur, comme dans la leçon, c'est le numéro de l'hôte qu'il
faut lire : celui que donnent `podman inspect` et `ctr task ls`.

## Exercice 3 : un conteneur n'est pas une tâche

Chez containerd, un **conteneur** et une **tâche** sont deux objets distincts.
`ctr run` crée les deux d'un coup. Séparez les gestes, dans un namespace à vous :

```bash
ctr -n essai image pull "$A" > /dev/null
ctr -n essai container create "$A" essai-c sleep infinity
ctr -n essai container ls -q
ctr -n essai task ls
ctr -n essai task start -d essai-c
ctr -n essai task ls
```

```text
essai-c
TASK    PID    STATUS
TASK       PID       STATUS
essai-c    122722    RUNNING
```

Après `container create`, le conteneur existe, mais aucune tâche : c'est une
description (image, commande, options), sans aucun processus. `task start`
crée le processus. C'est pour cela que la leçon nettoie en trois gestes :
tuer la tâche, la supprimer, puis supprimer le conteneur.

La tâche a aussi son état côté runc, dans une racine propre au namespace :

```bash
runc --root /run/containerd/runc/essai list
```

```text
ID          PID         STATUS      BUNDLE                                                        CREATED                          OWNER
essai-c     122722      running     /run/containerd/io.containerd.runtime.v2.task/essai/essai-c   2026-11-26T06:39:40.918987625Z   root
```

La leçon lisait `/run/containerd/runc/default`. Le dernier dossier est le nom
du namespace : chaque namespace a sa racine d'état.

## Exercice 4 : une image ne passe pas d'un namespace à l'autre

La leçon montre que deux moteurs ne partagent pas leurs images. C'est vrai
aussi entre deux namespaces du même containerd :

```bash
ctr -n essai image ls -q
ctr image ls -q
ctr -n essai2 run -d "$A" essai-d sleep infinity
ctr namespaces ls
```

```text
docker.io/library/alpine@sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2
ctr: image "docker.io/library/alpine@sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2": not found
NAME  LABELS
essai
nuit
```

L'image existe dans `essai`, pas dans `default` (le second `ls` est vide), et
`ctr -n essai2 run` ne la trouve pas. Le namespace `essai2` n'a même pas été
créé : le lancement a échoué avant. `ctr namespaces ls` liste tous les
namespaces : c'est la commande à jouer quand `ctr task ls` n'affiche rien.
`nuit` appartient au lab : laissez-le tel quel.

## Exercice 5 : sans son shim, la tâche disparaît

La leçon redémarre containerd et voit la tâche survivre, parce que le shim est
son parent. Faites l'essai, puis tuez le shim lui-même :

```bash
T=$(ctr -n essai task ls | awk '/essai-c/ {print $2}')
S=$(awk '{print $4}' /proc/$T/stat)
ps -o pid,comm -p $S
systemctl restart containerd
ctr -n essai task ls
kill -KILL $S
sleep 2
ctr -n essai task ls
ps -o pid,comm -p $T || echo "plus de processus $T"
ctr -n essai container ls -q
```

```text
    PID COMMAND
 122700 containerd-shim
TASK       PID       STATUS
essai-c    122722    RUNNING
TASK    PID    STATUS
    PID COMMAND
plus de processus 122722
essai-c
```

Le quatrième champ de `/proc/<PID>/stat` est le numéro du parent : ici le
shim. Le redémarrage de containerd ne touche pas la tâche. Le shim tué, la
tâche disparaît, et son processus aussi : le shim tenait le conteneur. Le
conteneur, lui, reste listé : c'est la description de l'exercice 3, qui
n'avait pas besoin du shim pour exister.

## Nettoyage

Supprimez le conteneur, l'image du namespace `essai`, le namespace lui-même,
puis l'image de Podman. Quittez ensuite le shell root :

```bash
ctr -n essai container rm essai-c
ctr -n essai image rm --sync "$A"
ctr namespaces rm essai
podman rmi "$A"
ctr namespaces ls
podman ps -a
exit
```

```text
docker.io/library/alpine@sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2
essai
Untagged: docker.io/library/alpine@sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2
Deleted: 164b5c6a230f645862b6123e07cf0a67f2f03371696aa82a12ccf3589e87c016
NAME LABELS
nuit
CONTAINER ID  IMAGE       COMMAND     CREATED     STATUS      PORTS       NAMES
```

Un namespace containerd ne se supprime que vide : l'option `--sync` attend
que les données de l'image soient vraiment effacées avant de rendre la main.
Il ne reste que `nuit`, posé par le lab.

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue
le nettoyage puis la préparation du lab : vous retrouvez exactement l'état de
départ du challenge. Il vous demande de confirmer : répondez `y`.

```bash
exit
dsoxlab reset runtime-qui-appelle-qui
dsoxlab check runtime-qui-appelle-qui
```

```text
╭─ Résultat : runtime-qui-appelle-qui ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests     │
╰──────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge vous attend, intact.

## Le challenge

À vous, seul cette fois : faire confier un conteneur à runc par Podman, lancer
une tâche containerd dans un namespace nommé, retrouver une tâche que
`ctr task ls` ne montre pas, et noter le vrai moniteur de chaque conteneur.

```bash
dsoxlab run runtime-qui-appelle-qui
dsoxlab challenge runtime-qui-appelle-qui
```
