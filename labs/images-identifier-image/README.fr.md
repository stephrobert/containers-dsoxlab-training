# Identité d'une image : le tag ment, le digest non

La leçon suit la chaîne du tag jusqu'aux couches. Ce cours s'attarde sur les
noms : deux tags pour une image, un conteneur dont le tag est parti, une
référence mal écrite, une reconstruction qui change d'identité, et une identité
qui voyage.

Vous travaillez dans `~/essai-noms`, sur des images `essai-noms`. Le challenge
porte sur `inventaire:1.0` : n'y touchez pas pendant le cours.

Page associée : [Lire une image OCI et son identité](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/identite-d-une-image/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-identifier-image
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. Construisez une petite
image. La fonction `id_de` donne l'identité qu'un nom désigne. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-noms && cd ~/essai-noms
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
printf 'FROM %s\nRUN echo un > /version\nCMD ["sleep","600"]\n' "$IMAGE" > Dockerfile
docker build -q -t essai-noms:1 . > /dev/null
id_de() { docker image inspect "$1" --format '{{.Id}}'; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 👯 Exercice 1 : deux noms pour une image

Donnez un second tag à l'image, puis supprimez le premier :

```bash
docker tag essai-noms:1 essai-noms:stable
[ "$(id_de essai-noms:1)" = "$(id_de essai-noms:stable)" ] && echo 'une seule image'
docker rmi essai-noms:1
docker images essai-noms --format '{{.Tag}}'
```

```text
une seule image
Untagged: essai-noms:1
stable
```

`docker rmi` répond `Untagged` : il a retiré un nom, et l'image reste tant
qu'un autre la désigne. La place n'est rendue qu'au dernier nom.

## 🕰️ Exercice 2 : un conteneur dont le tag est parti

Lancez un conteneur, reconstruisez l'image sous le même tag, puis comparez ce
qui tourne et ce que le tag désigne :

```bash
docker run -d --init --name essai-vieux essai-noms:stable > /dev/null
docker ps --filter name=essai-vieux --format '{{.Image}}'
sed -i 's/echo un/echo deux/' Dockerfile
docker build -q -t essai-noms:stable . > /dev/null
docker ps --filter name=essai-vieux --format '{{.Image}}' | grep -cE '^[0-9a-f]{12}$'
docker inspect essai-vieux --format '{{.Config.Image}}'
docker exec essai-vieux cat /version
docker run --rm essai-noms:stable cat /version
```

```text
essai-noms:stable
1
essai-noms:stable
un
deux
```

`docker ps` affichait le tag, il affiche maintenant un identifiant : le nom ne
désigne plus l'image de ce conteneur. `.Config.Image`, lui, garde le texte
écrit au lancement, et trompe. Une colonne IMAGE faite de chiffres est donc un
signal.

## ✍️ Exercice 3 : une référence mal écrite

Trompez-vous de quatre façons :

```bash
docker run --rm Essai-Noms:stable true 2>&1 | grep -o 'repository name.*'
docker run --rm essai-noms: true 2>&1 | grep -o 'invalid reference format'
docker run --rm essai-noms true 2>&1 | grep -o "Unable to find image.*"
docker run --rm "essai-noms:nimporte@$(id_de essai-noms:stable)" cat /version
```

```text
repository name (library/Essai-Noms) must be lowercase
invalid reference format
Unable to find image 'essai-noms:latest' locally
deux
```

Les majuscules et le tag vide sont refusés. Sans tag, Docker cherche `latest`,
et non le seul tag présent. Le dernier essai réussit : quand un digest est
donné, le tag qui le précède n'est pas vérifié. Ne vous fiez pas à la partie
lisible d'une telle référence.

## 🔁 Exercice 4 : reconstruire change l'identité

Construisez deux fois le même Dockerfile sans cache, puis deux fois en figeant
les dates :

```bash
for i in 1 2; do docker build -q --no-cache --provenance=false -t essai-noms:libre$i . > /dev/null; done
[ "$(id_de essai-noms:libre1)" = "$(id_de essai-noms:libre2)" ] && echo identiques || echo differentes
for i in 1 2; do SOURCE_DATE_EPOCH=0 docker build -q --no-cache --provenance=false --output type=image,name=essai-noms:fige$i,rewrite-timestamp=true . > /dev/null; done
[ "$(id_de essai-noms:fige1)" = "$(id_de essai-noms:fige2)" ] && echo identiques || echo differentes
```

```text
differentes
identiques
```

Les deux premières images ont le même contenu et deux identités, à cause des
dates. Dates figées et provenance absente, l'identité redevient la même. Deux
digests différents ne prouvent donc pas que le contenu diffère.

## 🧳 Exercice 5 : une identité qui voyage

Enregistrez l'image dans un fichier, supprimez-la, rechargez-la et comparez :

```bash
AVANT=$(id_de essai-noms:stable)
docker save essai-noms:stable -o noms.tar
docker rmi -f essai-noms:stable > /dev/null
docker load -q -i noms.tar
[ "$(id_de essai-noms:stable)" = "$AVANT" ] && echo 'meme identite'
tar xOf noms.tar index.json | grep -c "$AVANT"
```

```text
Loaded image: essai-noms:stable
meme identite
1
```

L'identité est la même après le voyage, et l'archive la porte dans son
`index.json` : vous pouvez la vérifier avant de charger le fichier.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-vieux > /dev/null
docker images 'essai-noms' --format '{{.Repository}}:{{.Tag}}' | xargs -r docker rmi -f > /dev/null
rm -r ~/essai-noms
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
dsoxlab reset images-identifier-image
dsoxlab check images-identifier-image
```

```text
╭─ Résultat : images-identifier-image ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests     │
╰──────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : une étiquette qui n'a pas bougé, et une image qui a
changé.

```bash
dsoxlab run images-identifier-image
dsoxlab challenge images-identifier-image
```
