# Lancer, arrêter, supprimer : trois verbes qui ne se recouvrent pas

La leçon lance, liste, arrête et supprime. Ce cours montre ce qui surprend dans
les premiers jours : un nom déjà pris, un conteneur qui s'arrête tout de suite,
ce qu'un arrêt garde, ce qu'une suppression emporte, et une liste qui ne montre
pas tout.

Vous travaillez sur des conteneurs `essai-*`. Le challenge porte sur `premier`,
`vitrine` et `rebut` : n'y touchez pas pendant le cours.

Page associée : [Lancer un conteneur Docker et choisir ce qu'il exécute](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/cli/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run docker-premier-conteneur
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-debut && cd ~/essai-debut
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🪪 Exercice 1 : un nom déjà pris

Lancez un conteneur qui finit aussitôt, puis essayez de reprendre son nom :

```bash
docker run --name essai-nom "$IMAGE" echo bonjour
docker ps --format '{{.Names}}' | grep -c '^essai-nom$'
docker run --name essai-nom "$IMAGE" echo encore 2>&1 | grep -o 'is already in use'
docker rename essai-nom essai-ancien
docker run --name essai-nom "$IMAGE" echo encore
docker rm essai-nom essai-ancien
```

```text
bonjour
0
is already in use
encore
essai-nom
essai-ancien
```

Le conteneur est fini, il n'apparaît plus dans `docker ps`, et son nom est
toujours pris. On le libère en renommant ou en supprimant, jamais en attendant.

## ⏱️ Exercice 2 : un conteneur qui s'arrête tout de suite

Lancez quatre commandes, et lisez le code de sortie de chaque conteneur :

```bash
docker run -d --name essai-a "$IMAGE" true > /dev/null
docker run -d --name essai-b "$IMAGE" sh -c 'echo probleme; exit 3' > /dev/null
docker run -d --name essai-c "$IMAGE" commande-absente 2>&1 | grep -o 'executable file not found'
docker run -d --name essai-d "$IMAGE" /etc/hostname 2>&1 | grep -o 'permission denied' | head -1
docker run -d --name essai-e "$IMAGE" sh > /dev/null
sleep 1
for c in a b c d e; do docker inspect essai-$c --format '{{.Name}} {{.State.Status}} {{.State.ExitCode}}'; done
docker rm essai-a essai-b essai-c essai-d essai-e > /dev/null
```

```text
executable file not found
permission denied
/essai-a exited 0
/essai-b exited 3
/essai-c created 127
/essai-d created 126
/essai-e exited 0
```

Un conteneur vit aussi longtemps que sa commande. Le code dit comment elle a
fini : 0 pour une fin normale, un autre pour une erreur, 127 pour une commande
introuvable, 126 pour un fichier que l'on ne peut pas exécuter. Les deux
derniers n'ont jamais démarré. Un shell sans terminal n'a rien à lire et finit
aussi.

## ⏸️ Exercice 3 : ce qu'un arrêt garde

Écrivez un fichier, arrêtez le conteneur, lisez ses journaux, copiez le
fichier, puis redémarrez :

```bash
docker run -d --init --name essai-garde "$IMAGE" sh -c 'echo depart; sleep 600' > /dev/null
docker exec essai-garde sh -c 'echo note > /root/note'
docker stop --timeout 1 essai-garde > /dev/null
docker logs essai-garde
docker cp -q essai-garde:/root/note . && cat note
docker exec essai-garde true 2>&1 | grep -o 'is not running'
docker start essai-garde > /dev/null
docker exec essai-garde cat /root/note
docker logs essai-garde
```

```text
depart
note
is not running
note
depart
depart
```

À l'arrêt, les fichiers et les journaux restent. On peut lire et copier, pas
exécuter. Au redémarrage, c'est le même conteneur : le fichier est là, et le
journal continue, d'où les deux lignes.

## 🗑️ Exercice 4 : ce qu'une suppression emporte

Essayez de supprimer le conteneur en marche, puis arrêtez-le, supprimez-le et
refaites-en un :

```bash
docker rm essai-garde 2>&1 | grep -oE 'container is running|cannot remove container' | head -1
docker stop --timeout 1 essai-garde > /dev/null && docker rm essai-garde
docker logs essai-garde 2>&1 | grep -o 'No such container'
docker run --name essai-garde "$IMAGE" ls -A /root | wc -l
docker rm essai-garde > /dev/null
docker run --rm --name essai-jetable "$IMAGE" echo fini
docker ps -a --format '{{.Names}}' | grep -c essai-jetable
```

```text
cannot remove container
essai-garde
No such container
0
fini
0
```

Supprimer emporte les fichiers du conteneur et ses journaux ; le nouveau part
de l'image. Docker refuse de supprimer un conteneur en marche, et `-f` lève ce
refus : ne le tapez pas par habitude. `--rm` supprime dès la fin, avec les
journaux.

## 🔎 Exercice 5 : une liste qui ne montre pas tout

Créez trois conteneurs dans trois états, et demandez la liste de quatre façons
:

```bash
docker run -d --init --name essai-vivant "$IMAGE" sleep 600 > /dev/null
docker create --name essai-jamais "$IMAGE" true > /dev/null
docker run -d --name essai-fini "$IMAGE" sh -c 'exit 4' > /dev/null; sleep 1
echo "ps : $(docker ps --filter name=essai- --format '{{.Names}}' | sort | tr '\n' ' ')"
echo "ps -a : $(docker ps -a --filter name=essai- --format '{{.Names}}:{{.State}}' | sort | tr '\n' ' ')"
echo "sortis en 4 : $(docker ps -a --filter name=essai- --filter exited=4 --format '{{.Names}}')"
echo "jamais lances : $(docker ps -a --filter name=essai- --filter status=created --format '{{.Names}}')"
docker ps -aq --filter name=essai- | xargs docker rm -f > /dev/null
```

```text
ps : essai-vivant
ps -a : essai-fini:exited essai-jamais:created essai-vivant:running
sortis en 4 : essai-fini
jamais lances : essai-jamais
```

`docker ps` ne montre que ce qui tourne. `-a` ajoute les finis et ceux qui
n'ont jamais démarré. Les filtres évitent de supprimer à l'œil : regardez
d'abord ce que le filtre rend, puis passez-le à `docker rm`.

## 🧹 Nettoyage

```bash
cd ~
rm -rf ~/essai-debut
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
dsoxlab reset docker-premier-conteneur
dsoxlab check docker-premier-conteneur
```

```text
╭─ Résultat : docker-premier-conteneur ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests      │
╰───────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : trois conteneurs, trois états, et un nom à libérer.

```bash
dsoxlab run docker-premier-conteneur
dsoxlab challenge docker-premier-conteneur
```
