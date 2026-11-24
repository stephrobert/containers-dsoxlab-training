# Où Docker range les fichiers d'un conteneur

La leçon montre où se trouve la couche d'écriture et ce qu'elle contient. Ce
cours mesure ce qu'elle coûte : un fichier supprimé qui ne libère rien, un
petit changement qui copie un gros fichier, un fichier creux, l'espace partagé
entre conteneurs, et une limite qui ne limite rien.

Vous travaillez dans `~/essai-couches`, avec l'image `essai-couches:1` et des
conteneurs `essai-*`. Le challenge porte sur `entrepot` : n'y touchez pas
pendant le cours.

Page associée : [Volumes Docker : conserver ses données et monter des fichiers](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run internes-stockage-des-images
```

Vous êtes connecté à `docker.lab`, où le moteur tourne, et l'image d'Alpine est
sur la machine. Construisez une petite image qui contient un fichier de 20 Mo.
**Gardez le même terminal jusqu'au nettoyage** : les variables n'existent que
dans lui.

```bash
mkdir -p ~/essai-couches && cd ~/essai-couches
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
printf 'FROM %s\nRUN head -c 20000000 /dev/urandom > /gros.bin\n' "$IMAGE" > Dockerfile
docker build -q -t essai-couches:1 . > /dev/null
taille() { docker container inspect --size "$1" --format '{{.SizeRw}}' | awk '{printf "%.1f Mo\n", $1/1000000}'; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🗑️ Exercice 1 : supprimer ne libère rien

Supprimez le gros fichier dans un conteneur :

```bash
docker run -d --name essai-supprime essai-couches:1 sleep 600 > /dev/null
docker exec essai-supprime rm /gros.bin
docker exec essai-supprime ls /gros.bin
docker diff essai-supprime
docker run --rm essai-couches:1 ls -s /gros.bin | awk '{print $2}'
```

```text
ls: /gros.bin: No such file or directory
D /gros.bin
/gros.bin
```

Le conteneur ne voit plus le fichier (`D` dans `docker diff`), mais l'image l'a
toujours : un autre conteneur le lit. La suppression ajoute une marque dans la
couche d'écriture, elle n'enlève rien en dessous.

## 🐘 Exercice 2 : un octet qui en coûte vingt millions

Comparez la couche d'écriture avant et après l'ajout d'un octet au gros fichier
:

```bash
docker run -d --name essai-copie essai-couches:1 sleep 600 > /dev/null
taille essai-copie
docker exec essai-copie sh -c 'printf x >> /gros.bin'
taille essai-copie
```

```text
0.0 Mo
20.0 Mo
```

Pour modifier un fichier de l'image, le moteur le copie d'abord en entier dans
la couche d'écriture. Les fichiers modifiés souvent, comme une base, ont donc
leur place dans un volume.

## 🕳️ Exercice 3 : un fichier creux

Créez un fichier de 50 Mo sans écrire d'octets, puis un autre en les écrivant :

```bash
docker run -d --name essai-creux essai-couches:1 sleep 600 > /dev/null
docker exec essai-creux truncate -s 50M /creux.bin
docker exec essai-creux sh -c 'ls -l /creux.bin | awk "{print \$5}"; du -k /creux.bin | cut -f1'
taille essai-creux
docker exec essai-creux dd if=/dev/zero of=/plein.bin bs=1M count=50 2> /dev/null
taille essai-creux
```

```text
52428800
0
0.0 Mo
52.4 Mo
```

`ls` affiche la taille annoncée, `du` la place prise. Le premier fichier
n'occupe presque rien, le second 50 Mo. Pour chercher ce qui remplit un disque,
lisez `du`.

## 🤝 Exercice 4 : trois conteneurs, une image

Lancez trois conteneurs de la même image et pesez leur couche d'écriture :

```bash
for i in 1 2 3; do docker run -d --name essai-part$i essai-couches:1 sleep 600 > /dev/null; done
for i in 1 2 3; do taille essai-part$i; done
docker ps -s --filter name=essai-part1 --format '{{.Size}}'
```

```text
0.0 Mo
0.0 Mo
0.0 Mo
4.1kB (virtual 29.1MB)
```

Chaque conteneur ne coûte que sa propre couche. La valeur `virtual` ajoute
l'image entière, partagée entre les trois : ne l'additionnez pas.

## 🚧 Exercice 5 : une limite qui ne limite rien

Demandez une couche d'écriture de 10 Mo, écrivez-y 30 Mo, puis donnez une
valeur absurde. Bornez ensuite autrement :

```bash
docker run --rm --storage-opt size=10m "$IMAGE" sh -c 'dd if=/dev/zero of=/bloc bs=1M count=30 2> /dev/null; du -m /bloc'
docker run --rm --storage-opt size=abc "$IMAGE" true; echo "code: $?"
docker run --rm --read-only --tmpfs /travail:size=10m "$IMAGE" sh -c 'dd if=/dev/zero of=/travail/bloc bs=1M count=30 2>&1 | grep dd:; touch /marque'
```

```text
30	/bloc
code: 0
dd: error writing '/travail/bloc': No space left on device
touch: /marque: Read-only file system
```

Sur ce moteur, l'option est acceptée et sans effet : les 30 Mo passent, et
`abc` ne provoque aucune erreur. Un code 0 ne prouve donc pas qu'une limite
s'applique, il faut essayer de la dépasser. La racine en lecture seule et le
tmpfs d'une taille fixée bornent réellement ce que le conteneur écrit.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-supprime essai-copie essai-creux essai-part1 essai-part2 essai-part3 > /dev/null
docker rmi essai-couches:1 > /dev/null
rm -r ~/essai-couches
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
dsoxlab reset internes-stockage-des-images
dsoxlab check internes-stockage-des-images
```

```text
╭─ Résultat : internes-stockage-des-images ─╮
│  0 / 100 pts                              │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests          │
╰───────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : trouver où vivent les écritures d'un conteneur, et
les peser sur le disque de l'hôte.

```bash
dsoxlab run internes-stockage-des-images
dsoxlab challenge internes-stockage-des-images
```
