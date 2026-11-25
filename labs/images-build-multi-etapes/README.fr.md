# Ce qui vient du socle ne se retire pas

La leçon sépare la construction de l'exécution et remplit une image vide. Ce
cours regarde le passage d'une étape à l'autre : ce qui n'est pas transmis, ce
que deviennent les droits et les liens, une copie depuis une autre image, deux
fautes de copie, et une étape que personne ne construit.

Vous travaillez dans `~/essai-etapes`, sur des images `essai-etapes`. Le
challenge porte sur `/opt/lab-multietapes` : n'y touchez pas pendant le cours.

Page associée : [Séparer construction et exécution : le build multi-étapes](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/build-multi-etapes/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-build-multi-etapes
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-etapes && cd ~/essai-etapes
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🚪 Exercice 1 : ce qui n'est pas transmis

Une étape fixe une variable, un répertoire, un utilisateur et un argument. La
suivante les relit :

```bash
cat > Dockerfile <<EOF
ARG EDITION=7
FROM $IMAGE AS atelier
ARG EDITION
ENV REGLAGE=oui
WORKDIR /atelier
USER 4242
RUN echo "\$REGLAGE \$(pwd) \$(id -u) \$EDITION" > /tmp/trace
FROM $IMAGE
COPY --from=atelier /tmp/trace /trace
RUN echo "[\$REGLAGE] \$(pwd) \$(id -u) [\$EDITION]" >> /trace
EOF
docker build -q -t essai-etapes:1 . > /dev/null
docker run --rm essai-etapes:1 cat /trace
```

```text
oui /atelier 4242 7
[] / 0 []
```

Rien ne passe, sauf le fichier copié. Un réglage nécessaire à l'exécution doit
être répété dans la dernière étape, et un `ARG` déclaré avant le premier `FROM`
doit être redéclaré dans chaque étape qui le lit.

## 🔑 Exercice 2 : les droits et les liens

Copiez un fichier, un lien seul, puis le répertoire entier :

```bash
cat > droits.Dockerfile <<EOF
FROM $IMAGE AS atelier
RUN mkdir /s && echo 'echo lance' > /s/vrai && chmod 750 /s/vrai && chown 4242 /s/vrai && ln -s vrai /s/lien && ln -s /s/vrai /s/absolu
FROM $IMAGE
COPY --from=atelier /s/vrai /d/vrai
COPY --from=atelier --chown=1000:1000 --chmod=755 /s/vrai /d/choisi
COPY --from=atelier /s/lien /d/seul
COPY --from=atelier /s /d/tout
EOF
docker build -q -f droits.Dockerfile -t essai-etapes:2 . > /dev/null
docker run --rm essai-etapes:2 sh -c 'stat -c "%u:%g %a %F %n" /d/vrai /d/choisi /d/seul /d/tout/lien'
docker run --rm essai-etapes:2 cat /d/tout/absolu
```

```text
4242:0 750 regular file /d/vrai
1000:1000 755 regular file /d/choisi
4242:0 750 regular file /d/seul
0:0 777 symbolic link /d/tout/lien
cat: can't open '/d/tout/absolu': No such file or directory
```

Le propriétaire et le mode suivent le fichier, sauf si `--chown` et `--chmod`
les fixent. Un lien copié seul devient le fichier qu'il désigne. Dans un
répertoire, il reste un lien : s'il vise un chemin absolu de l'étape
précédente, il est cassé.

## 📦 Exercice 3 : copier depuis une autre image

`--from` accepte aussi une image qui n'est pas une étape :

```bash
cat > autre.Dockerfile <<EOF
FROM $IMAGE
COPY --from=$IMAGE /etc/alpine-release /socle
EOF
docker build -q -f autre.Dockerfile -t essai-etapes:3 . > /dev/null
docker run --rm essai-etapes:3 cat /socle
```

```text
3.24.3
```

Vous prenez un fichier dans une image sans partir d'elle. Épinglez cette image
par son digest comme celle du `FROM` : elle fournit du contenu au même titre.

## ✏️ Exercice 4 : deux fautes de copie

Trompez-vous dans le nom de l'étape, puis dans le chemin :

```bash
cat > faute.Dockerfile <<EOF
FROM $IMAGE AS atelier
RUN echo produit > /p
FROM $IMAGE
COPY --from=atelie /p /p
EOF
docker build -q -f faute.Dockerfile . 2>&1 | grep -o 'docker.io/library/atelie:latest' | head -1
sed -i 's/--from=atelie /--from=atelier /; s|/p /p|/q /q|' faute.Dockerfile
docker build -q -f faute.Dockerfile . 2>&1 | grep -o '"/q": not found' | head -1
```

```text
docker.io/library/atelie:latest
"/q": not found
```

Une étape inconnue devient un nom d'image : Docker la cherche sur Docker Hub,
et l'erreur parle d'accès refusé. Le pire cas est celui où une telle image
existe. La seconde erreur est plus franche et nomme le chemin.

## 💤 Exercice 5 : une étape que personne ne construit

Une étape échoue, mais la dernière n'en dépend pas. Construisez l'image, puis
l'étape :

```bash
cat > dormant.Dockerfile <<EOF
FROM $IMAGE AS controle
RUN exit 7
FROM $IMAGE
RUN echo ok > /ok
EOF
docker build -q -f dormant.Dockerfile -t essai-etapes:5 . > /dev/null; echo "code: $?"
docker build -q -f dormant.Dockerfile --target controle . 2>&1 | grep -o 'exit code: 7' | head -1
docker build -q -f dormant.Dockerfile --target rien . 2>&1 | grep -o 'target stage.*' | head -1
```

```text
code: 0
exit code: 7
target stage "rien" could not be found
```

La construction réussit sans avoir joué l'étape en échec. Un contrôle placé
dans une étape ne protège que si la suite en dépend, ou si vous la construisez
par `--target`.

## 🧹 Nettoyage

```bash
cd ~
docker images 'essai-etapes' --format '{{.Repository}}:{{.Tag}}' | xargs -r docker rmi -f > /dev/null
rm -r ~/essai-etapes
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
dsoxlab reset images-build-multi-etapes
dsoxlab check images-build-multi-etapes
```

```text
╭─ Résultat : images-build-multi-etapes ─╮
│  0 / 100 pts                           │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests       │
╰────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un produit à livrer, sans l'outillage qui l'a
fabriqué.

```bash
dsoxlab run images-build-multi-etapes
dsoxlab challenge images-build-multi-etapes
```
