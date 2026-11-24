# Trois pannes, trois codes de sortie à lire

La leçon donne la grille des codes 125, 126 et 127, et dit où lire l'erreur. Ce
cours vous fait rencontrer cinq échecs dont le premier diagnostic est trompeur :
un interprète absent, un fichier écrit sous Windows, des guillemets de trop, un
droit qui dépend de l'utilisateur, et un conteneur jamais démarré.

Vous travaillez dans `~/essai-codes`, sur des conteneurs `essai-*`. Le challenge
porte sur `panne-a`, `panne-b` et `panne-c` : n'y touchez pas pendant le cours.

Page associée : [Lire un échec de démarrage Docker : codes et boucles](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run troubleshoot-exit-127
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. La fonction `lire`
affiche le statut, le code et l'erreur d'un conteneur. **Gardez le même terminal
jusqu'au nettoyage.**

```bash
mkdir -p ~/essai-codes && cd ~/essai-codes
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
lire() { docker container inspect "$1" --format 'statut={{.State.Status}} code={{.State.ExitCode}} erreur={{.State.Error}}'; }
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026.

## 🐚 Exercice 1 : le fichier existe, et Docker dit le contraire

Ce script existe et il est exécutable. Sa première ligne demande `bash`, que
l'image d'Alpine ne contient pas :

```bash
printf '#!/bin/bash\necho bonjour\n' > lancer.sh
chmod 755 lancer.sh
docker run --name essai-bash -v "$PWD:/outils:ro" "$IMAGE" /outils/lancer.sh > /dev/null 2>&1
lire essai-bash
docker logs essai-bash
docker run --rm "$IMAGE" ls /bin/bash
```

```text
statut=exited code=255 erreur=
exec /outils/lancer.sh: no such file or directory
ls: /bin/bash: No such file or directory
```

Le message nomme `lancer.sh`, qui existe pourtant. Le fichier introuvable est
son interprète, `/bin/bash`. Le code est 255, hors de la grille, et
`.State.Error` est vide : le message est dans les journaux. La dernière commande
confirme que `bash` n'est pas dans l'image.

## 🪟 Exercice 2 : les fins de ligne de Windows

Même message, autre cause : ce script demande `/bin/sh`, qui existe bien.

```bash
printf '#!/bin/sh\r\necho bonjour\r\n' > windows.sh
chmod 755 windows.sh
docker run --name essai-windows -v "$PWD:/outils:ro" "$IMAGE" /outils/windows.sh > /dev/null 2>&1
lire essai-windows
docker logs essai-windows
head -1 windows.sh | od -c
sed -i 's/\r$//' windows.sh
docker run --rm -v "$PWD:/outils:ro" "$IMAGE" /outils/windows.sh
```

```text
statut=exited code=255 erreur=
exec /outils/windows.sh: no such file or directory
0000000   #   !   /   b   i   n   /   s   h  \r  \n
0000013
bonjour
```

`od -c` montre `\r` avant `\n` : le fichier vient d'un éditeur Windows. Le
noyau a cherché un programme nommé `/bin/sh` suivi de ce caractère invisible. Le
`sed` le retire et le script s'exécute. Devant ce message, vérifiez donc
l'interprète, puis les fins de ligne.

## ✂️ Exercice 3 : des guillemets de trop

Comparez la même commande avec et sans guillemets autour de l'ensemble :

```bash
docker run --name essai-guillemets "$IMAGE" "ls -l /etc/hostname" > /dev/null 2>&1
lire essai-guillemets | cut -c1-60
docker container inspect essai-guillemets --format '{{json .Config.Cmd}}'
docker run --name essai-separes "$IMAGE" ls /etc/alpine-release
docker container inspect essai-separes --format '{{json .Config.Cmd}}'
```

```text
statut=created code=127 erreur=failed to create task for con
["ls -l /etc/hostname"]
/etc/alpine-release
["ls","/etc/alpine-release"]
```

Avec les guillemets, `.Config.Cmd` ne contient qu'un élément : Docker cherche un
programme dont le nom comporte des espaces, d'où le code 127. Sans eux, il y a
deux éléments, le programme et son argument. `.Config.Cmd` se lit avant de
soupçonner l'image.

## 🔑 Exercice 4 : un droit qui dépend de l'utilisateur

Ce script n'est lisible que par son propriétaire. Lancez-le sous l'uid 4242,
puis sous root :

```bash
printf '#!/bin/sh\necho bonjour\n' > prive.sh
chmod 700 prive.sh
docker run --name essai-prive --user 4242 -v "$PWD:/outils:ro" "$IMAGE" /outils/prive.sh > /dev/null 2>&1
lire essai-prive
docker logs essai-prive
docker run --rm -v "$PWD:/outils:ro" "$IMAGE" /outils/prive.sh
```

```text
statut=exited code=2 erreur=
/bin/sh: can't open '/outils/prive.sh': Permission denied
bonjour
```

Le code n'est pas 126 mais 2, et le conteneur a démarré : c'est le shell qui a
rendu ce code, faute de pouvoir lire le script. Sous root, il s'exécute. Le même
fichier peut donc réussir ou échouer selon `--user`.

## 📦 Exercice 5 : fouiller un conteneur jamais démarré

`docker exec` ne sert à rien sur un conteneur qui n'a pas démarré. Ses fichiers
restent lisibles :

```bash
docker create --name essai-jamais "$IMAGE" outil-absent > /dev/null
lire essai-jamais
docker export essai-jamais | tar -t | grep -E '^bin/(sh|bash)$|outil-absent'
docker cp essai-jamais:/etc/alpine-release - | tar -xO
```

```text
statut=created code=0 erreur=
bin/sh
3.24.3
```

`docker export` rend tout le système de fichiers sous forme d'archive, que
`tar -t` liste : `sh` est présent, `bash` et `outil-absent` ne le sont pas. Vous
répondez à la question « ce programme est-il dans l'image ? » sans rien lancer.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-bash essai-windows essai-guillemets essai-separes essai-prive essai-jamais > /dev/null
rm -r ~/essai-codes
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset troubleshoot-exit-127
dsoxlab check troubleshoot-exit-127
```

```text
╭─ Résultat : troubleshoot-exit-127 ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests   │
╰────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : lire trois pannes, relever leurs codes et le statut de
l'une d'elles, puis lancer un conteneur qui tourne sur la même image.

```bash
dsoxlab run troubleshoot-exit-127
dsoxlab challenge troubleshoot-exit-127
```
