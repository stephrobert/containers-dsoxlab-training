# Ordonner un Dockerfile pour le cache

La leçon montre comment le constructeur décide de réutiliser une couche, dans
quel ordre écrire les instructions, et comment un `.dockerignore` garde le
cache stable. Ce cours vous fait voir trois choses qu'elle ne montre pas : la
place d'un `ARG` peut faire rejouer une installation, un `RUN` peut rester figé
par le cache et se rafraîchir à partir d'un point choisi, et
`docker builder prune` ne vide pas le cache que vos images utilisent encore.

Vous travaillez dans `~/essai-cache`, avec des images `essai-cache:*`. Le
challenge porte sur une autre application et un autre Dockerfile : vous le
ferez seul, à la fin.

Page associée : [Dockerfile : les bonnes pratiques](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-ordre-des-couches
```

Vous êtes maintenant connecté à `docker.lab`, une Debian 13 où le moteur
Docker tourne. Créez le répertoire d'essai, rangez le socle dans une variable,
et définissez une petite fonction `etapes`. Elle lit la sortie d'un build et
affiche chaque étape, suivie de `CACHED` quand le constructeur l'a réutilisée.
**Gardez le même terminal jusqu'au nettoyage** : la variable et la fonction
n'existent que dans lui.

```bash
mkdir -p ~/essai-cache && cd ~/essai-cache
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
etapes() { awk '/^#[0-9]+ \[[0-9]\/[0-9]\]/ { n=$1; sub(/^#[0-9]+ /, ""); if ($0 !~ /^\[1\//) { ligne[n]=$0; ordre[++k]=n } next } /^#[0-9]+ CACHED/ { cache[$1]=1 } END { for (i=1;i<=k;i++) print ligne[ordre[i]] (cache[ordre[i]] ? "  CACHED" : "") }'; }
```

Les sorties de ce cours ont été relevées sur cette machine le 23 novembre 2026,
avec Docker Engine 29.9.2.

## 🏷️ Exercice 1 : la place d'un `ARG`

Un `ARG` est une valeur passée au build par `--build-arg`. Elle est visible
par les `RUN` qui la suivent, et son changement peut les faire rejouer. Écrivez
un Dockerfile qui déclare `ETIQUETTE` en haut, avant une installation qui ne
s'en sert pas. Construisez une fois, puis reconstruisez avec une nouvelle
valeur, unique, tirée de l'heure :

```bash
cat > Dockerfile.haut <<EOF
FROM $ALPINE
ARG ETIQUETTE=a
RUN apk add --no-cache jq >/dev/null && jq --version
RUN echo "etiquette=\$ETIQUETTE" > /etiquette
EOF
docker build -q -t essai-cache:haut -f Dockerfile.haut . >/dev/null
docker build --progress=plain -t essai-cache:haut -f Dockerfile.haut --build-arg ETIQUETTE="$(date +%s)" . 2>&1 | etapes
```

```text
[2/3] RUN apk add --no-cache jq >/dev/null && jq --version
[3/3] RUN echo "etiquette=1795458824" > /etiquette
```

L'installation de `jq` a été rejouée, alors qu'elle n'utilise pas
`ETIQUETTE` : déclarée au-dessus d'elle, la valeur fait partie de son
environnement, donc de ce que le constructeur compare. Déplacez l'`ARG` juste
avant l'étape qui s'en sert, et recommencez :

```bash
cat > Dockerfile.bas <<EOF
FROM $ALPINE
RUN apk add --no-cache jq >/dev/null && jq --version
ARG ETIQUETTE=a
RUN echo "etiquette=\$ETIQUETTE" > /etiquette
EOF
docker build -q -t essai-cache:bas -f Dockerfile.bas . >/dev/null
docker build --progress=plain -t essai-cache:bas -f Dockerfile.bas --build-arg ETIQUETTE="$(date +%s)" . 2>&1 | etapes
```

```text
[2/3] RUN apk add --no-cache jq >/dev/null && jq --version  CACHED
[3/3] RUN echo "etiquette=1795458826" > /etiquette
```

Cette fois, l'installation est servie par le cache, et seule la dernière étape
est refaite. Un `ARG` se déclare donc au plus près de l'étape qui l'utilise,
comme un fichier se copie au plus près de l'étape qui le lit.

## 🕰️ Exercice 2 : un `RUN` figé, et le rafraîchir à partir d'un point

La leçon prévient qu'un `RUN` dont le texte ne change pas est toujours servi
par le cache. Rendez cela visible avec une commande qui note l'heure. Le
Dockerfile en note deux, séparées par un `ARG RAFRAICHIR` :

```bash
cat > Dockerfile.date <<EOF
FROM $ALPINE
RUN date +%H:%M:%S > /construit-a
ARG RAFRAICHIR=0
RUN date +%H:%M:%S > /rafraichi-a
EOF
docker build -q -t essai-cache:date -f Dockerfile.date . >/dev/null
docker run --rm essai-cache:date cat /construit-a /rafraichi-a
sleep 3; docker build -q -t essai-cache:date -f Dockerfile.date . >/dev/null
docker run --rm essai-cache:date cat /construit-a /rafraichi-a
sleep 3; docker build -q -t essai-cache:date -f Dockerfile.date --build-arg RAFRAICHIR="$(date +%s)" . >/dev/null
docker run --rm essai-cache:date cat /construit-a /rafraichi-a
```

```text
18:31:41
18:33:47
18:31:41
18:33:47
18:31:41
18:33:55
```

Le deuxième build rend les mêmes heures que le premier : rien n'a été
exécuté, les deux couches viennent du cache. Au troisième, la valeur de
`RAFRAICHIR` change : la seconde heure est nouvelle, la première reste celle du
tout premier build. Placé juste avant les étapes à rafraîchir (une mise à jour
de paquets, par exemple), un tel `ARG` les force à se rejouer sans reconstruire
tout le reste. `--no-cache`, lui, reconstruit tout.

## 🧹 Exercice 3 : ce que `docker builder prune` vide vraiment

`docker builder prune` supprime le cache de construction. Lancez-le, puis
reconstruisez `essai-cache:bas` avec une valeur déjà construite :

```bash
docker build -q -t essai-cache:bas -f Dockerfile.bas --build-arg ETIQUETTE=b . >/dev/null
docker builder prune -f | tail -1
docker build --progress=plain -t essai-cache:bas -f Dockerfile.bas --build-arg ETIQUETTE=b . 2>&1 | etapes
```

```text
Total:	2.876MB
[2/3] RUN apk add --no-cache jq >/dev/null && jq --version  CACHED
[3/3] RUN echo "etiquette=b" > /etiquette  CACHED
```

Le nettoyage a libéré un peu d'espace, et pourtant tout est resté en cache.
Les couches de l'image `essai-cache:bas` existent toujours, et le constructeur
les réutilise. Supprimez l'image d'abord, puis recommencez :

```bash
docker rmi essai-cache:bas >/dev/null
docker builder prune -f | tail -1
docker build --progress=plain -t essai-cache:bas -f Dockerfile.bas --build-arg ETIQUETTE=b . 2>&1 | etapes
```

```text
Total:	1.409MB
[2/3] RUN apk add --no-cache jq >/dev/null && jq --version
[3/3] RUN echo "etiquette=b" > /etiquette
```

Cette fois, les deux étapes sont refaites. `docker builder prune` ne retire que
le cache qu'aucune image n'utilise : pour repartir vraiment de zéro, il faut
supprimer les images, ou construire avec `--no-cache`.

## 🧹 Nettoyage

Supprimez les images et le répertoire d'essai. La dernière commande compte les
images `essai-*` qui restent :

```bash
cd ~
docker rmi essai-cache:haut essai-cache:bas essai-cache:date | grep -c Untagged
rm -rf ~/essai-cache
docker images --format '{{.Repository}}' | grep -c '^essai-'
```

```text
3
0
```

Plus aucune image d'essai. Quittez ensuite la machine et remettez le lab à
zéro. `dsoxlab reset` rejoue le nettoyage puis la préparation du lab : vous
retrouvez exactement l'état de départ du challenge. Il vous demande de
confirmer : répondez `y`.

```bash
exit
dsoxlab reset images-ordre-des-couches
dsoxlab check images-ordre-des-couches
```

```text
╭─ Résultat : images-ordre-des-couches ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests      │
╰───────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge vous attend, intact.

## 🎯 Le challenge

À vous, seul cette fois : réordonner le Dockerfile d'une application pour
qu'un changement de code ne refasse plus l'installation, alors qu'un
changement de dépendance la refait toujours.

```bash
dsoxlab run images-ordre-des-couches
dsoxlab challenge images-ordre-des-couches
```
