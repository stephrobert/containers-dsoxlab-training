# Où les données survivent : les trois types de montage

La leçon présente le volume nommé, le bind mount, le tmpfs et la lecture seule.
Ce cours ajoute cinq situations : un fichier monté que l'on remplace, un tmpfs
plein, un montage sous un autre, un volume que l'on ne peut pas supprimer, et
la sauvegarde d'un volume.

Vous travaillez dans `~/essai-montages`, sur des conteneurs et des volumes
`essai-*`. Le challenge porte sur `archive` et `coffre-donnees` : n'y touchez
pas pendant le cours.

Page associée : [Volumes Docker : conserver ses données et monter des fichiers](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run donnees-volumes-et-montages
```

Vous êtes connecté à `docker.lab`, où le moteur tourne, et l'image d'Alpine est
sur la machine. **Gardez le même terminal jusqu'au nettoyage** : les variables
n'existent que dans lui.

```bash
mkdir -p ~/essai-montages && cd ~/essai-montages
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 📝 Exercice 1 : un fichier monté que l'on remplace

Montez un seul fichier, ajoutez-y une ligne, puis remplacez-le comme le font
beaucoup d'éditeurs :

```bash
echo 'port=8080' > reglages.conf
docker run -d --name essai-fichier --mount type=bind,source="$PWD/reglages.conf",target=/reglages.conf "$IMAGE" sleep 600 > /dev/null
echo 'mode=test' >> reglages.conf
docker exec essai-fichier cat /reglages.conf
echo 'port=9090' > nouveau.conf
mv nouveau.conf reglages.conf
cat reglages.conf
docker exec essai-fichier head -1 /reglages.conf
```

```text
port=8080
mode=test
port=9090
port=8080
```

L'ajout est visible, le remplacement ne l'est pas. Docker a monté le fichier
lui-même, et non son nom : après `mv`, le nom désigne un autre fichier, et le
conteneur garde l'ancien. Montez le répertoire quand un fichier peut être
remplacé.

## 🧯 Exercice 2 : un tmpfs plein

Donnez 4 Mo à un espace en mémoire et écrivez-y 6 Mo :

```bash
docker run -d --name essai-plein --mount type=tmpfs,target=/travail,tmpfs-size=4m "$IMAGE" sleep 600 > /dev/null
docker exec essai-plein dd if=/dev/zero of=/travail/bloc bs=1M count=6 2>&1 | grep dd:
docker exec essai-plein df -h /travail
docker container inspect essai-plein --format '{{.State.Status}}'
```

```text
dd: error writing '/travail/bloc': No space left on device
Filesystem                Size      Used Available Use% Mounted on
tmpfs                     4.0M      4.0M         0 100% /travail
running
```

`No space left on device` ne parle pas du disque de l'hôte, mais des 4 Mo du
tmpfs. Le conteneur continue de tourner, et l'espace reste plein tant que
personne ne supprime le fichier. Sans `tmpfs-size`, un tmpfs peut prendre
jusqu'à la moitié de la mémoire de l'hôte.

## 🪆 Exercice 3 : un montage sous un autre

Donnez un cache en mémoire à l'intérieur d'un répertoire en lecture seule, avec
puis sans le point de montage :

```bash
mkdir -p reference
docker run --rm -v "$PWD/reference:/ref:ro" --tmpfs /ref/cache "$IMAGE" true 2>&1 | grep -oE 'read-only file system' | head -1
mkdir reference/cache
docker run --rm -v "$PWD/reference:/ref:ro" --tmpfs /ref/cache "$IMAGE" sh -c 'echo ok > /ref/cache/a && cat /ref/cache/a; echo non > /ref/b'
```

```text
read-only file system
ok
sh: can't create /ref/b: Read-only file system
```

Docker doit créer `/ref/cache` pour y monter quelque chose, et `/ref` est en
lecture seule : le conteneur ne démarre pas. Quand le répertoire existe déjà
dans la source, les deux montages cohabitent, et chacun garde son mode.

## 🔐 Exercice 4 : un volume que l'on ne peut pas supprimer

Arrêtez un conteneur qui utilise un volume, puis essayez de supprimer le volume
:

```bash
docker run -d --name essai-tenant -v essai-carnet:/donnees "$IMAGE" sleep 600 > /dev/null
docker stop --timeout 1 essai-tenant > /dev/null
docker volume rm essai-carnet 2>&1 | grep -o 'volume is in use'
docker ps --filter volume=essai-carnet --format '{{.Names}}' | wc -l
docker ps -a --filter volume=essai-carnet --format '{{.Names}} {{.Status}}' | cut -d' ' -f1,2
```

```text
volume is in use
0
essai-tenant Exited
```

Un conteneur arrêté tient encore son volume, et `docker ps` sans `-a` ne le
montre pas. Le refus protège la donnée : cherchez qui la tient avant de
supprimer quoi que ce soit.

## 💾 Exercice 5 : sauvegarder un volume et le restaurer

Archivez un volume par un conteneur jetable qui le monte en lecture seule, puis
restaurez l'archive dans un volume neuf :

```bash
docker run --rm -v essai-carnet:/d "$IMAGE" sh -c 'echo ligne-1 > /d/carnet.txt; chown 4242 /d/carnet.txt'
docker run --rm -v essai-carnet:/d:ro -v "$PWD:/sauvegarde" "$IMAGE" tar -czf /sauvegarde/carnet.tgz -C /d .
docker run --rm -v essai-copie:/d -v "$PWD:/sauvegarde:ro" "$IMAGE" tar -xzf /sauvegarde/carnet.tgz -C /d
docker run --rm -v essai-copie:/d:ro "$IMAGE" sh -c 'cat /d/carnet.txt; stat -c %u /d/carnet.txt'
```

```text
ligne-1
4242
```

Le contenu et le propriétaire sont revenus. Le montage `:ro` garantit que la
sauvegarde ne modifie rien. Cette méthode copie des fichiers : pour une base de
données en marche, employez son propre outil de sauvegarde.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-fichier essai-plein essai-tenant > /dev/null
docker volume rm essai-carnet essai-copie
sudo rm -r ~/essai-montages
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker volume ls --format '{{.Name}}' | grep -c '^essai-'
```

```text
essai-carnet
essai-copie
0
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset donnees-volumes-et-montages
dsoxlab check donnees-volumes-et-montages
```

```text
╭─ Résultat : donnees-volumes-et-montages ─╮
│  0 / 100 pts                             │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests         │
╰──────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : sortir une donnée unique d'un conteneur avant de le
recréer avec les trois montages.

```bash
dsoxlab run donnees-volumes-et-montages
dsoxlab challenge donnees-volumes-et-montages
```
