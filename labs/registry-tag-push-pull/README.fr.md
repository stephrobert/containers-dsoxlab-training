# Publier une image qu'un autre client peut vraiment récupérer

La leçon nomme une image pour un registre, la pousse, relève son digest dans
`RepoDigests` et prouve avec Skopeo que le registre sert toutes ses couches.
Ce cours vous fait interroger le registre lui-même, sans Docker : ce qu'il
liste, et le digest qu'il annonce dans sa réponse. Vous verrez aussi qu'un
contenu peut porter deux tags, et où part un push quand le nom n'a pas de
registre. Pour finir, vous jouerez un client complet qui n'a jamais vu
l'image : téléchargement, chargement et exécution sans réseau.

Vous travaillez dans `~/essai-registre`, avec un registre d'essai sur le port
`5099` et des images `127.0.0.1:5099/essai/*`. Le challenge porte sur un autre
registre, une autre image et un autre dépôt : vous le ferez seul, à la fin.

Page associée : [Publier et récupérer une image de façon maîtrisée](https://www.stephane-robert.info/docs/conteneurs/registres/docker-hub/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run registry-tag-push-pull
```

Vous êtes maintenant connecté à `docker.lab`, une Debian 13 où le moteur
Docker tourne. Créez le répertoire d'essai, rangez les deux images de base du
cours dans des variables, et démarrez le registre d'essai. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-registre && cd ~/essai-registre
REGISTRE=registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker run -d --name essai-registre -p 127.0.0.1:5099:5000 -v essai-registre:/var/lib/registry "$REGISTRE" > /dev/null
sleep 2
docker version --format '{{.Server.Version}}'
skopeo --version
```

```text
29.9.2
skopeo version 1.18.0
```

Les sorties de ce cours ont été relevées sur cette machine le 24 novembre 2026,
avec Docker Engine 29.9.2 et Skopeo 1.18.0, le paquet de Debian que le lab
installe. La leçon lance Skopeo 1.22.3 depuis son image de conteneur : les
commandes de ce cours sont les mêmes.

## 📇 Exercice 1 : ce que liste un registre

Un registre répond à une API HTTP. Deux adresses disent ce qu'il contient :
`/v2/_catalog` liste les dépôts, et `/v2/<dépôt>/tags/list` les tags d'un
dépôt. Interrogez le registre d'essai, encore vide :

```bash
curl -s http://127.0.0.1:5099/v2/_catalog
```

```text
{"repositories":[]}
```

Une liste vide : aucun dépôt. Vous y reviendrez après le premier push, pour
voir ce que le registre a reçu sans passer par Docker.

## 🏷️ Exercice 2 : deux tags, un seul contenu

La leçon déplace un tag vers un autre contenu. L'inverse existe aussi : un
même contenu peut porter plusieurs tags. Construisez une image, donnez-lui
les tags `1.0` et `courant`, puis poussez les deux :

```bash
printf 'FROM %s\nCOPY note.txt /note.txt\nCMD ["cat", "/note.txt"]\n' "$ALPINE" > Dockerfile
echo "note d'essai $(date +%s)" > note.txt
docker build -q -t 127.0.0.1:5099/essai/note:1.0 . > /dev/null
docker tag 127.0.0.1:5099/essai/note:1.0 127.0.0.1:5099/essai/note:courant
docker push -q 127.0.0.1:5099/essai/note:1.0
docker push 127.0.0.1:5099/essai/note:courant
```

```text
127.0.0.1:5099/essai/note:1.0
The push refers to repository [127.0.0.1:5099/essai/note]
54660ed56fa2: Layer already exists
44136fa355b3: Already exists
c0f9151d9ab4: Already exists
7b229517ed22: Layer already exists
courant: digest: sha256:bebe30d3783f6cfe602ddefe67e6d36d02f9666b73e41a55afb4c1ec0877c1fe size: 855
```

Le premier push, lancé avec `-q`, n'affiche que le nom poussé. Le second
n'a rien envoyé : chaque ligne dit `Already exists` ou
`Layer already exists`. Le registre avait déjà tout reçu avec le premier, et
il a seulement ajouté un nom. La dernière ligne donne le digest du tag
`courant` : c'est celui du contenu poussé sous `1.0`.

## 📡 Exercice 3 : ce que répond le registre

Relisez la liste des dépôts et des tags, puis demandez au registre le digest
de chaque tag. Une requête `HEAD` sur `/v2/<dépôt>/manifests/<tag>` renvoie
seulement les en-têtes de la réponse, sans le manifeste. L'en-tête
`Docker-Content-Digest` porte le digest :

```bash
curl -s http://127.0.0.1:5099/v2/_catalog
curl -s http://127.0.0.1:5099/v2/essai/note/tags/list
for t in 1.0 courant; do
  curl -sI -H 'Accept: application/vnd.oci.image.index.v1+json' http://127.0.0.1:5099/v2/essai/note/manifests/$t | grep -iE 'content-type|docker-content-digest'
done
```

```text
{"repositories":["essai/note"]}
{"name":"essai/note","tags":["1.0","courant"]}
Content-Type: application/vnd.oci.image.index.v1+json
Docker-Content-Digest: sha256:bebe30d3783f6cfe602ddefe67e6d36d02f9666b73e41a55afb4c1ec0877c1fe
Content-Type: application/vnd.oci.image.index.v1+json
Docker-Content-Digest: sha256:bebe30d3783f6cfe602ddefe67e6d36d02f9666b73e41a55afb4c1ec0877c1fe
```

Le registre connaît le dépôt `essai/note` et ses deux tags. Les deux tags
renvoient le même digest, celui que le push a affiché. Le `Content-Type` dit
que le registre sert un index OCI : la liste qui regroupe l'image et son
attestation de provenance, comme dans la leçon. L'en-tête `Accept` dit au
registre quels formats le client sait lire.

Ces deux requêtes ne passent pas par Docker. N'importe quel client HTTP peut
donc vérifier ce qu'un registre sert sous un tag, par exemple dans une CI.

## 🚫 Exercice 4 : un nom sans registre

La leçon prévient qu'une image nommée sans registre part vers Docker Hub.
Vérifiez-le avec un nom court, en ne gardant que la première et la dernière
ligne de la sortie :

```bash
docker tag 127.0.0.1:5099/essai/note:1.0 essai-note:1.0
docker push essai-note:1.0 > push.log 2>&1; echo "code retour: $?"
head -1 push.log
tail -1 push.log
docker image rm essai-note:1.0 > /dev/null
```

```text
code retour: 1
The push refers to repository [docker.io/library/essai-note]
push access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
```

Docker a complété le nom en `docker.io/library/essai-note`, l'espace des
images officielles de Docker Hub, où vous n'avez aucun droit. Le registre a
refusé, et le push sort en erreur. Le préfixe `127.0.0.1:5099/` est donc ce
qui dit où va l'image. Sans lui, Docker choisit Docker Hub à votre place.

## 🧪 Exercice 5 : un client qui n'a jamais vu l'image

La leçon montre que `docker pull` ne prouve pas qu'un registre sert toutes
les couches, puisque Docker les a déjà. Jouez un vrai client neuf. Skopeo
télécharge l'image depuis le registre dans une archive, sans consulter le
stockage de Docker. Docker charge ensuite cette archive sous un autre nom, et
l'exécute sans réseau :

```bash
skopeo copy -q --src-tls-verify=false docker://127.0.0.1:5099/essai/note:1.0 docker-archive:$HOME/essai-registre/note.tar:essai-copie/note:1.0
ls -l note.tar | awk '{print $5, $9}'
docker load -i note.tar
docker run --rm --network none essai-copie/note:1.0
cat note.txt
```

```text
8722432 note.tar
Loaded image: essai-copie/note:1.0
note d'essai 1795503902
note d'essai 1795503902
```

L'archive contient tout ce que le registre a servi. Docker l'a chargée sous
le nom `essai-copie/note:1.0`, et le conteneur, privé de réseau par
`--network none`, affiche la même note que le fichier d'origine. Si le
registre avait perdu une couche, `skopeo copy` aurait échoué. C'est la preuve
qu'une autre machine peut récupérer cette image.

## 🧹 Nettoyage

Retirez le registre d'essai, son volume, les images et le répertoire, puis
vérifiez qu'il ne reste rien :

```bash
cd ~
docker rm -f essai-registre > /dev/null
docker volume rm essai-registre
docker image rm 127.0.0.1:5099/essai/note:1.0 127.0.0.1:5099/essai/note:courant essai-copie/note:1.0 > /dev/null
rm -rf ~/essai-registre
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c -e '^127.0.0.1:5099/' -e '^essai-'
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
dsoxlab reset registry-tag-push-pull
dsoxlab check registry-tag-push-pull
```

```text
╭─ Résultat : registry-tag-push-pull ─╮
│  0 / 100 pts                        │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests    │
╰─────────────────────────────────────╯
```

0 sur 2 : c'est le résultat attendu. Le challenge vous attend, intact.

## 🎯 Le challenge

À vous, seul cette fois : publier dans le registre du lab une image qui
n'existe que dans votre moteur, de sorte qu'un client indépendant puisse la
récupérer et l'exécuter à l'identique.

```bash
dsoxlab run registry-tag-push-pull
dsoxlab challenge registry-tag-push-pull
```
