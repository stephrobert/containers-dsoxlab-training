# Retrouver la release d'origine après déplacement de son tag

La leçon déplace un tag vers un autre contenu, puis retrouve le contenu
d'origine en le tirant par son digest. Ce cours va plus loin sur trois
points. D'abord, ce que fait Docker quand une référence porte à la fois un tag
et un digest. Ensuite, comment lire, sur un conteneur qui tourne, la référence
qui l'a lancé. Enfin, ce que le registre et le moteur gardent d'un contenu qui
a perdu son tag.

Vous travaillez dans `~/essai-digest`, avec un registre d'essai sur le port
`5098` et des images `127.0.0.1:5098/essai/*`. Le challenge porte sur un autre
registre, une autre release et un conteneur déjà lancé : vous le ferez seul, à
la fin.

Page associée : [Publier et récupérer une image de façon maîtrisée](https://www.stephane-robert.info/docs/conteneurs/registres/docker-hub/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run registry-tag-contre-digest
```

Vous êtes maintenant connecté à `docker.lab`, une Debian 13 où le moteur
Docker tourne. Créez le répertoire d'essai, rangez les images de base dans des
variables, et démarrez le registre d'essai. **Gardez le même terminal jusqu'au
nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-digest && cd ~/essai-digest
REGISTRE=registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker run -d --name essai-depot-digest -p 127.0.0.1:5098:5000 -v essai-depot-digest:/var/lib/registry "$REGISTRE" > /dev/null
sleep 2
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026.

Publiez maintenant la situation de la leçon : une première version sous le tag
`prod`, dont vous gardez le digest dans une variable, puis une seconde version
sous le même tag. Regardez aussi ce que le moteur garde en local :

```bash
printf 'FROM %s\nCOPY version.txt /version.txt\nCMD ["cat", "/version.txt"]\n' "$ALPINE" > Dockerfile
echo "version A" > version.txt
docker build -q -t 127.0.0.1:5098/essai/carnet:prod . > /dev/null
docker push -q 127.0.0.1:5098/essai/carnet:prod > /dev/null
D=$(docker image inspect 127.0.0.1:5098/essai/carnet:prod --format '{{range .RepoDigests}}{{println .}}{{end}}' | grep '^127.0.0.1:5098/' | cut -d@ -f2)
echo "digest de la version A : $D"
echo "version B" > version.txt
docker build -q -t 127.0.0.1:5098/essai/carnet:prod . > /dev/null
docker push -q 127.0.0.1:5098/essai/carnet:prod > /dev/null
docker run --rm 127.0.0.1:5098/essai/carnet:prod
docker images -a --digests 127.0.0.1:5098/essai/carnet
```

```text
digest de la version A : sha256:f19c03f2c1ce7e3f6298bfe235b6ab22d46b1a26e7509990b0768467eb1d8bce
version B
REPOSITORY                    TAG       DIGEST                                                                    IMAGE ID       CREATED          SIZE
127.0.0.1:5098/essai/carnet   prod      sha256:5a4771c70f81ec66a1e21c3027e7847be9ee0adf4552ee6e20a2dffa50c9f474   5a4771c70f81   17 minutes ago   13MB
```

Le tag `prod` désigne maintenant la version B, et seule la variable `D` garde
l'adresse de la version A. Remarquez la dernière sortie : la version A
n'apparaît plus. Dès que `prod` a été reconstruit, l'ancienne image n'était
plus nommée en local, et ce moteur ne la liste plus.

## 🔀 Exercice 1 : un tag et un digest dans la même référence

Une référence peut porter les deux : `dépôt:tag@digest`. Laquelle des deux
parties Docker suit-il ? Essayez avec un tag qui n'existe pas, puis avec le bon
tag, en gardant le digest de la version A :

```bash
docker run --rm "127.0.0.1:5098/essai/carnet:inexistant@$D"; echo "code retour: $?"
docker run --rm "127.0.0.1:5098/essai/carnet:prod@$D"
```

```text
Unable to find image '127.0.0.1:5098/essai/carnet:inexistant@sha256:f19c03f2c1ce7e3f6298bfe235b6ab22d46b1a26e7509990b0768467eb1d8bce' locally
127.0.0.1:5098/essai/carnet@sha256:f19c03f2c1ce7e3f6298bfe235b6ab22d46b1a26e7509990b0768467eb1d8bce: Pulling from essai/carnet
62c342681880: Pulling fs layer
7b229517ed22: Pulling fs layer
62c342681880: Already exists
7b229517ed22: Already exists
151c2ec11428: Download complete
44136fa355b3: Already exists
62c342681880: Pull complete
Digest: sha256:f19c03f2c1ce7e3f6298bfe235b6ab22d46b1a26e7509990b0768467eb1d8bce
Status: Downloaded newer image for 127.0.0.1:5098/essai/carnet@sha256:f19c03f2c1ce7e3f6298bfe235b6ab22d46b1a26e7509990b0768467eb1d8bce
version A
code retour: 0
version A
```

À la première commande, Docker n'avait plus la version A en local : il l'a tirée
du registre. Regardez la ligne `Pulling from` : la référence y apparaît sans le
tag, réduite à `dépôt@digest`. La seconde n'a rien eu à tirer. Les deux
affichent la version A, alors que `prod` désigne la B et que le tag `inexistant`
n'existe nulle part. Quand une référence porte un digest, Docker le suit et
ignore le tag. Le tag n'y sert plus qu'à aider la lecture humaine. Un tag faux ne déclenche aucune erreur, ce qui peut tromper
un relecteur : il croit lire `prod`, alors que la version lancée est celle du
digest.

## 🔎 Exercice 2 : la référence qui a lancé un conteneur

Le challenge contrôle comment un conteneur a été lancé. Docker garde cette
information. Lancez deux conteneurs, l'un par le tag, l'autre par le digest,
puis comparez deux champs : `.Config.Image`, la référence écrite au
lancement, et `.Image`, l'identifiant de l'image réellement utilisée.

```bash
docker run -d --name essai-par-tag 127.0.0.1:5098/essai/carnet:prod sleep 600 > /dev/null
docker run -d --name essai-par-digest "127.0.0.1:5098/essai/carnet@$D" sleep 600 > /dev/null
for c in essai-par-tag essai-par-digest; do
  docker inspect "$c" --format "$c"'
  Config.Image = {{.Config.Image}}
  Image        = {{.Image}}'
done
```

```text
essai-par-tag
  Config.Image = 127.0.0.1:5098/essai/carnet:prod
  Image        = sha256:5a4771c70f81ec66a1e21c3027e7847be9ee0adf4552ee6e20a2dffa50c9f474
essai-par-digest
  Config.Image = 127.0.0.1:5098/essai/carnet@sha256:f19c03f2c1ce7e3f6298bfe235b6ab22d46b1a26e7509990b0768467eb1d8bce
  Image        = sha256:f19c03f2c1ce7e3f6298bfe235b6ab22d46b1a26e7509990b0768467eb1d8bce
```

Le premier conteneur garde le texte `:prod`. Pour savoir quelle version il
exécute, il faut lire `.Image`, puis la comparer au digest de chaque version.
Le second garde la référence avec le digest : elle désigne un seul contenu,
que le prochain déplacement du tag ne change pas. Sur ce moteur,
qui stocke les images dans containerd, `.Image` vaut d'ailleurs le digest
poussé. La leçon prévient que ce n'est pas une garantie de Docker.

## 🗂️ Exercice 3 : ce que le registre garde sans tag

Le registre ne liste que les tags. Le contenu de la version A n'en a plus,
mais il est toujours là. Demandez la liste des tags, puis interrogez le
manifeste de la version A par son digest :

```bash
curl -s http://127.0.0.1:5098/v2/essai/carnet/tags/list
curl -sI -H 'Accept: application/vnd.oci.image.index.v1+json' "http://127.0.0.1:5098/v2/essai/carnet/manifests/$D" | grep -iE '^HTTP|docker-content-digest'
```

```text
{"name":"essai/carnet","tags":["prod"]}
HTTP/1.1 200 OK
Docker-Content-Digest: sha256:f19c03f2c1ce7e3f6298bfe235b6ab22d46b1a26e7509990b0768467eb1d8bce
```

La liste ne contient que `prod`. L'API ne propose aucune liste des contenus sans tag : si personne n'avait gardé le digest de la version A, il
serait introuvable par l'API. Pourtant, la requête par le digest répond `200
OK`. Le contenu existe tant que le registre ne le supprime pas. C'est
pourquoi le challenge fournit un bon de livraison qui porte le digest : sans
lui, il n'y aurait rien à retrouver.

## 🖥️ Exercice 4 : ce que le moteur garde localement

Le moteur aussi a vu passer les deux versions. `docker images --digests`
affiche, pour chaque image locale, son tag et son digest :

```bash
docker images --digests 127.0.0.1:5098/essai/carnet
```

```text
REPOSITORY                    TAG       DIGEST                                                                    IMAGE ID       CREATED          SIZE
127.0.0.1:5098/essai/carnet   <none>    sha256:f19c03f2c1ce7e3f6298bfe235b6ab22d46b1a26e7509990b0768467eb1d8bce   f19c03f2c1ce   17 minutes ago   13MB
127.0.0.1:5098/essai/carnet   prod      sha256:5a4771c70f81ec66a1e21c3027e7847be9ee0adf4552ee6e20a2dffa50c9f474   5a4771c70f81   17 minutes ago   13MB
```

La ligne marquée `prod` est la version B. La version A apparaît sous
`<none>` : avant l'exercice 1, elle n'était plus listée, et c'est le tirage par
digest qui l'a ramenée, sans tag local. Son digest est là. C'est une autre
façon de le retrouver, à condition d'être sur la machine qui avait l'image.

## 🧹 Nettoyage

Retirez les conteneurs, le registre d'essai, son volume, les images et le
répertoire, puis vérifiez qu'il ne reste rien :

```bash
cd ~
docker rm -f essai-par-tag essai-par-digest essai-depot-digest > /dev/null
docker volume rm essai-depot-digest
docker image rm "127.0.0.1:5098/essai/carnet@$D" 127.0.0.1:5098/essai/carnet:prod > /dev/null
rm -rf ~/essai-digest
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c '^127.0.0.1:5098/'
```

```text
essai-depot-digest
0
0
```

Plus rien de ce cours. Quittez ensuite la machine et remettez le lab à zéro.
`dsoxlab reset` rejoue le nettoyage puis la préparation du lab : vous
retrouvez exactement l'état de départ du challenge. Il vous demande de
confirmer : répondez `y`.

```bash
exit
dsoxlab reset registry-tag-contre-digest
dsoxlab check registry-tag-contre-digest
```

```text
╭─ Résultat : registry-tag-contre-digest ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests        │
╰─────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge vous attend, intact.

## 🎯 Le challenge

À vous, seul cette fois : un conteneur tourne sur une release dont le tag a
été déplacé. Remettez en service la release d'origine, lancée par une
référence qui désigne toujours le même contenu, sans toucher au tag.

```bash
dsoxlab run registry-tag-contre-digest
dsoxlab challenge registry-tag-contre-digest
```
