# Ce qu'une couche garde

La leçon pèse trois écritures d'une même image. Ce cours cherche d'autres
mégaoctets cachés : un droit changé trop tard, un contexte trop large, un
fichier copié deux fois, la place partagée entre images, et une taille qui en
cache une autre.

Vous travaillez dans `~/essai-poids`, sur des images `essai-poids`. Le
challenge porte sur `/opt/lab-taille` : n'y touchez pas pendant le cours.

Page associée : [Inspecter et réduire une image Docker sans la casser](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/optimiser-taille-image/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-optimiser-la-taille
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. Créez un fichier de 20
Mo. La fonction `couches` pèse les dernières couches d'une image. **Gardez le
même terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-poids && cd ~/essai-poids
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
dd if=/dev/urandom of=gros bs=1M count=20 2> /dev/null
couches() { docker history --format '{{.Size}} {{.CreatedBy}}' "essai-poids:$1" | head -"$2" | cut -c1-48; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🔑 Exercice 1 : un droit changé trop tard

Changez le propriétaire après la copie, puis pendant la copie :

```bash
printf 'FROM %s\nCOPY gros /gros\nRUN chown 4242 /gros\n' "$IMAGE" > apres.Dockerfile
printf 'FROM %s\nCOPY --chown=4242 gros /gros\n' "$IMAGE" > pendant.Dockerfile
for f in apres pendant; do docker build -q -f $f.Dockerfile -t essai-poids:$f . > /dev/null; done
couches apres 2
couches pendant 1
```

```text
21MB RUN /bin/sh -c chown 4242 /gros # buildkit
21MB COPY gros /gros # buildkit
21MB COPY --chown=4242 gros /gros # buildkit
```

`chown` n'a pas changé un octet du fichier, et l'image le porte deux fois : une
couche enregistre le fichier entier dès que ses attributs changent. `chmod` et
`mv` ont le même effet.

## 🧺 Exercice 2 : un contexte trop large

Laissez traîner un répertoire dans le contexte, copiez tout, puis écartez-le :

```bash
mkdir vieux-rapports && dd if=/dev/urandom of=vieux-rapports/2019 bs=1M count=15 2> /dev/null
printf 'FROM %s\nCOPY . /appli\n' "$IMAGE" > tout.Dockerfile
docker build -q -f tout.Dockerfile -t essai-poids:tout . > /dev/null
docker run --rm essai-poids:tout du -sm /appli | cut -f1
printf 'vieux-rapports\n*.Dockerfile\n' > .dockerignore
docker build -q -f tout.Dockerfile -t essai-poids:tout . > /dev/null
docker run --rm essai-poids:tout du -sm /appli | cut -f1
docker run --rm essai-poids:tout ls -A /appli
```

```text
36
21
.dockerignore
gros
```

`COPY .` prend ce qui est dans le répertoire le jour de la construction.
`.dockerignore` l'écarte avant l'envoi au moteur. Remarquez qu'il est lui-même
dans l'image : ajoutez-y son propre nom, ou copiez les fichiers un par un.

## 👯 Exercice 3 : un fichier présent deux fois

Donnez deux noms au même contenu, de trois façons :

```bash
printf 'FROM %s\nCOPY gros /a\nCOPY gros /b\n' "$IMAGE" > copie.Dockerfile
printf 'FROM %s\nCOPY gros /a\nRUN ln /a /b\n' "$IMAGE" > dur.Dockerfile
printf 'FROM %s\nCOPY gros /a\nRUN ln -s /a /b\n' "$IMAGE" > symbolique.Dockerfile
for f in copie dur symbolique; do docker build -q -f $f.Dockerfile -t essai-poids:$f . > /dev/null; echo "-- $f"; couches $f 1; done
```

```text
-- copie
21MB COPY gros /b # buildkit
-- dur
21MB RUN /bin/sh -c ln /a /b # buildkit
-- symbolique
4.1kB RUN /bin/sh -c ln -s /a /b # buildkit
```

Le lien physique, gratuit sur un disque ordinaire, coûte ici le fichier entier
: il est créé dans une autre couche que l'original. Seul le lien symbolique ne
pèse presque rien.

## 🤝 Exercice 4 : la place partagée entre images

Comparez la taille annoncée et la part propre de deux images qui ont la même
première couche :

```bash
docker system df -v --format '{{json .Images}}' > images.json
python3 -c "
import json
for x in json.load(open('images.json')):
    if x['Repository'] == 'essai-poids' and x['Tag'] in ('pendant', 'symbolique'):
        print(x['Tag'], x['Size'], 'propre:', x['UniqueSize'])
" | sort
```

```text
pendant 54.9MB propre: 41.96MB
symbolique 54.9MB propre: 8.115kB
```

Les deux images ont la même taille, mais l'une ne coûte presque rien en propre
: ses couches servent à d'autres. Supprimer une image rend sa part propre, pas
sa taille. Cherchez la place là où `UniqueSize` est grand.

## 🗜️ Exercice 5 : une taille qui en cache une autre

Comparez une image pleine de zéros et une image pleine d'octets au hasard :

```bash
printf 'FROM %s\nRUN dd if=/dev/zero of=/zero bs=1M count=20 2> /dev/null\n' "$IMAGE" > zero.Dockerfile
docker build -q -f zero.Dockerfile -t essai-poids:zero . > /dev/null
for f in zero pendant; do docker image ls "essai-poids:$f"; done | awk '/essai/{print $1, "disque", $3, "transfert", $4}'
```

```text
essai-poids:zero disque 33.9MB transfert 3.88MB
essai-poids:pendant disque 54.9MB transfert 24.8MB
```

Le transfert se fait sur des couches compressées : les zéros s'y réduisent à
presque rien, le hasard non. `DISK USAGE` dit ce que l'image occupe ici,
`CONTENT SIZE` ce qui voyage. Précisez laquelle vous comparez.

## 🧹 Nettoyage

```bash
cd ~
docker images 'essai-poids' --format '{{.Repository}}:{{.Tag}}' | xargs -r docker rmi -f > /dev/null
rm -r ~/essai-poids
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c '^essai-'
```

```text
0
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset images-optimiser-la-taille
dsoxlab check images-optimiser-la-taille
```

```text
╭─ Résultat : images-optimiser-la-taille ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests        │
╰─────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : une image juste de l'intérieur, et bien trop lourde.

```bash
dsoxlab run images-optimiser-la-taille
dsoxlab challenge images-optimiser-la-taille
```
