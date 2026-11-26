# Qui veille sur quoi

## La situation

Sur `oci.lab`, une Debian 13 sans Docker, l'équipe fait tourner ses conteneurs
avec deux moteurs : Podman et containerd. Elle veut savoir, pour chacun, quel
programme les lance et quel processus les surveille. Un collègue affirme aussi
qu'un conteneur `gardien` tourne sous containerd, mais `ctr task ls` n'affiche
rien.

Podman, conmon, crun, runc et containerd sont installés. Vous êtes `root` par
`sudo`. L'image à employer est busybox 1.37.0 :

```text
docker.io/library/busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

## Ce que vous devez obtenir

1. Un conteneur Podman **`vigie`** tourne sur busybox, détaché, et Podman l'a
   confié au runtime **runc**, pas à crun.
2. Une tâche containerd **`releve`** tourne sur busybox, dans le namespace
   containerd **`equipe`**.
3. Le fichier **`/srv/reponses/shim-gardien`** contient le PID du shim qui
   surveille `gardien`. `gardien` doit continuer de tourner.
4. Le fichier **`/srv/reponses/conmon-vigie`** contient le PID du conmon qui
   surveille `vigie`.

Un PID s'écrit seul sur sa ligne.

## Les repères utiles

Le parent du processus d'un conteneur est son moniteur : conmon chez Podman,
un shim chez containerd. La ligne de commande de ce moniteur nomme le runtime.

`ctr` lit le namespace `default` tant qu'on ne lui en désigne pas un autre, et
une image tirée dans un namespace n'existe pas dans les autres.

## Comment vous saurez que c'est bon

Les tests lisent `podman inspect vigie`, les tâches des namespaces
containerd, et comparent vos deux réponses au parent réel de chaque processus, lu
dans `/proc`.

```bash
dsoxlab check runtime-qui-appelle-qui
```
