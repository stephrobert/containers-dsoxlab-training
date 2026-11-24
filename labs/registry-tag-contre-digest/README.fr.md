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
docker run -d --name essai-registre -p 127.0.0.1:5098:5000 -v essai-registre:/var/lib/registry "$REGISTRE" > /dev/null
sleep 2
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours ont été relevées sur cette machine le 24 novembre 2026,
avec Docker Engine 29.9.2.

## 📦 Exercice 1 : deux versions sous le même tag

Publiez une première version sous le tag `prod`, gardez son digest dans une
variable, puis publiez une seconde version sous le même tag :

```bash
printf 'FROM %s\nCOPY version.txt /version.txt\nCMD ["cat", "/version.txt"]\n' "$ALPINE" > Dockerfile
echo "version A" > version.txt
docker build -q -t 127.0.0.1:5098/essai/appli:prod . > /dev/null
docker push -q 127.0.0.1:5098/essai/appli:prod > /dev/null
D=$(docker image inspect 127.0.0.1:5098/essai/appli:prod --format '{{range .RepoDigests}}{{println .}}{{end}}' | grep '^127.0.0.1:5098/' | cut -d@ -f2)
echo "digest de la version A : $D"
echo "version B" > version.txt
docker build -q -t 127.0.0.1:5098/essai/appli:prod . > /dev/null
docker push -q 127.0.0.1:5098/essai/appli:prod > /dev/null
docker run --rm 127.0.0.1:5098/essai/appli:prod
```

```text
digest de la version A : sha256:75df6ecd10bc59366bcc3f8110aa76796e28c928528decb0786ac2ff4638ae67
version B
```

C'est la situation de la leçon : le tag `prod` désigne maintenant la version
B, et seule la variable `D` garde l'adresse de la version A.

## 🔀 Exercice 2 : un tag et un digest dans la même référence

Une référence peut porter les deux : `dépôt:tag@digest`. Laquelle des deux
parties Docker suit-il ? Essayez avec le bon tag, puis avec un tag qui n'existe
pas, en gardant le digest de la version A :

```bash
docker run --rm "127.0.0.1:5098/essai/appli:prod@$D"
docker run --rm "127.0.0.1:5098/essai/appli:inexistant@$D"; echo "code retour: $?"
```

```text
Unable to find image '127.0.0.1:5098/essai/appli:prod@sha256:75df6ecd10bc59366bcc3f8110aa76796e28c928528decb0786ac2ff4638ae67' locally
127.0.0.1:5098/essai/appli@sha256:75df6ecd10bc59366bcc3f8110aa76796e28c928528decb0786ac2ff4638ae67: Pulling from essai/appli
62c342681880: Pulling fs layer
7b229517ed22: Pulling fs layer
62c342681880: Already exists
7b229517ed22: Already exists
bf61523ce1d7: Download complete
44136fa355b3: Already exists
62c342681880: Pull complete
Digest: sha256:75df6ecd10bc59366bcc3f8110aa76796e28c928528decb0786ac2ff4638ae67
Status: Downloaded newer image for 127.0.0.1:5098/essai/appli@sha256:75df6ecd10bc59366bcc3f8110aa76796e28c928528decb0786ac2ff4638ae67
version A
version A
code retour: 0
```

Docker n'avait plus localement d'image à ce nom : il a tiré la version A du
registre. Regardez la ligne `Pulling from` : la référence y apparaît sans le
tag, réduite à `dépôt@digest`. Les deux commandes affichent la version A,
alors que `prod` désigne la B et que le tag `inexistant` n'existe nulle part.
Quand une référence porte un digest, Docker le suit et ignore le tag. Le tag n'y sert plus qu'à aider la
lecture humaine. Un tag faux ne déclenche aucune erreur, ce qui peut tromper
un relecteur : il croit lire `prod`, alors que la version lancée est celle du
digest.

## 🔎 Exercice 3 : la référence qui a lancé un conteneur

Le challenge contrôle comment un conteneur a été lancé. Docker garde cette
information. Lancez deux conteneurs, l'un par le tag, l'autre par le digest,
puis comparez deux champs : `.Config.Image`, la référence écrite au
lancement, et `.Image`, l'identifiant de l'image réellement utilisée.

```bash
docker run -d --name essai-par-tag 127.0.0.1:5098/essai/appli:prod sleep 600 > /dev/null
docker run -d --name essai-par-digest "127.0.0.1:5098/essai/appli@$D" sleep 600 > /dev/null
for c in essai-par-tag essai-par-digest; do
  docker inspect "$c" --format "$c"'
  Config.Image = {{.Config.Image}}
  Image        = {{.Image}}'
done
```

```text
essai-par-tag
  Config.Image = 127.0.0.1:5098/essai/appli:prod
  Image        = sha256:538690e91280fcad027aaa6d130d2a90207b4f79af523ca5e178d09178f0cf4c
essai-par-digest
  Config.Image = 127.0.0.1:5098/essai/appli@sha256:75df6ecd10bc59366bcc3f8110aa76796e28c928528decb0786ac2ff4638ae67
  Image        = sha256:75df6ecd10bc59366bcc3f8110aa76796e28c928528decb0786ac2ff4638ae67
```

Le premier conteneur garde le texte `:prod`. Pour savoir quelle version il
exécute, il faut lire `.Image`, puis la comparer au digest de chaque version.
Le second garde la référence avec le digest : elle désigne un seul contenu,
et dit encore la vérité après le prochain déplacement du tag. Sur ce moteur,
qui stocke les images dans containerd, `.Image` vaut d'ailleurs le digest
poussé. La leçon prévient que ce n'est pas une garantie de Docker.

## 🗂️ Exercice 4 : ce que le registre garde sans tag

Le registre ne liste que les tags. Le contenu de la version A n'en a plus,
mais il est toujours là. Demandez la liste des tags, puis interrogez le
manifeste de la version A par son digest :

```bash
curl -s http://127.0.0.1:5098/v2/essai/appli/tags/list
curl -sI -H 'Accept: application/vnd.oci.image.index.v1+json' "http://127.0.0.1:5098/v2/essai/appli/manifests/$D" | grep -iE '^HTTP|docker-content-digest'
```

```text
{"name":"essai/appli","tags":["prod"]}
HTTP/1.1 200 OK
Docker-Content-Digest: sha256:75df6ecd10bc59366bcc3f8110aa76796e28c928528decb0786ac2ff4638ae67
```

La liste ne contient que `prod`. Aucune commande du registre ne liste les
contenus sans tag : si personne n'avait gardé le digest de la version A, il
serait introuvable par l'API. Pourtant, la requête par le digest répond `200
OK`. Le contenu existe tant que le registre ne le supprime pas. C'est
pourquoi le challenge fournit un bon de livraison qui porte le digest : sans
lui, il n'y aurait rien à retrouver.

## 🖥️ Exercice 5 : ce que le moteur garde localement

Le moteur aussi a vu passer les deux versions. `docker images --digests`
affiche, pour chaque image locale, son tag et son digest :

```bash
docker images --digests 127.0.0.1:5098/essai/appli
```

```text
REPOSITORY                   TAG       DIGEST                                                                    IMAGE ID       CREATED         SIZE
127.0.0.1:5098/essai/appli   prod      sha256:538690e91280fcad027aaa6d130d2a90207b4f79af523ca5e178d09178f0cf4c   538690e91280   2 seconds ago   13MB
127.0.0.1:5098/essai/appli   <none>    sha256:75df6ecd10bc59366bcc3f8110aa76796e28c928528decb0786ac2ff4638ae67   75df6ecd10bc   2 seconds ago   13MB
```

La ligne marquée `prod` est la version B. La version A apparaît sous
`<none>` : le moteur l'a gardée, parce que les conteneurs de l'exercice 3 et
le tirage par digest l'ont utilisée, mais elle n'a plus de tag local. Son
digest, lui, est toujours là. C'est une autre façon de le retrouver, à
condition d'être sur la machine qui avait l'image.

## 🧹 Nettoyage

Retirez les conteneurs, le registre d'essai, son volume, les images et le
répertoire, puis vérifiez qu'il ne reste rien :

```bash
cd ~
docker rm -f essai-par-tag essai-par-digest essai-registre > /dev/null
docker volume rm essai-registre
docker image rm "127.0.0.1:5098/essai/appli@$D" 127.0.0.1:5098/essai/appli:prod > /dev/null
rm -rf ~/essai-digest
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c '^127.0.0.1:5098/'
```

```text
essai-registre
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
référence qui ne pourra plus mentir, sans toucher au tag.

```bash
dsoxlab run registry-tag-contre-digest
dsoxlab challenge registry-tag-contre-digest
```
