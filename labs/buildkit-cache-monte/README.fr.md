# Garder un cache entre deux builds avec un montage

La leçon montre qu'un `RUN --mount=type=cache` donne à une commande un
répertoire qui survit d'un build à l'autre sans entrer dans l'image, et qu'il
évite de retélécharger une dépendance quand le verrou change. Ce cours vous
fait voir ce répertoire grandir de build en build, le partager entre deux
Dockerfile par son identifiant, et mesurer ce qui le vide.

Vous travaillez dans `~/essai-montage`, avec des images `essai-montage:*` et
des caches nommés `essai-*`. Le challenge porte sur un autre outil, un autre
dépôt de dépendances et un constructeur dédié : vous le ferez seul, à la fin.

Page associée : [Dockerfile : les bonnes pratiques](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run buildkit-cache-monte
```

Vous êtes maintenant connecté à `docker.lab`, une Debian 13 où le moteur
Docker tourne. Créez le répertoire d'essai et rangez le socle dans une
variable. **Gardez le même terminal jusqu'au nettoyage** : la variable
n'existe que dans lui.

```bash
mkdir -p ~/essai-montage && cd ~/essai-montage
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
```

Les sorties de ce cours ont été relevées sur cette machine le 23 novembre 2026,
avec Docker Engine 29.9.2 et le constructeur par défaut.

## 📈 Exercice 1 : un répertoire qui survit d'un build à l'autre

Écrivez un Dockerfile dont l'étape `RUN` ajoute une ligne à un fichier du
cache monté, puis compte ses lignes. L'`ARG TOUR` change à chaque build, ce
qui force l'étape à se rejouer. Construisez trois fois, puis regardez si le
cache est dans l'image :

```bash
cat > Dockerfile.passages <<EOF
FROM $ALPINE
ARG TOUR=0
RUN --mount=type=cache,id=essai-passages,target=/cache \
    echo "tour \$TOUR" >> /cache/passages && echo "passages=\$(wc -l < /cache/passages)" > /resultat
EOF
for tour in 1 2 3; do
  docker build -q -t essai-montage:passages -f Dockerfile.passages --build-arg TOUR=$tour . >/dev/null
  docker run --rm essai-montage:passages cat /resultat
done
docker run --rm essai-montage:passages sh -c 'ls -A /cache 2>/dev/null | wc -l'
```

```text
passages=1
passages=2
passages=3
0
```

Le compte monte de 1 à 3 : à chaque build, l'étape retrouve les lignes
laissées par la précédente. Et l'image ne contient aucun fichier sous
`/cache` : le répertoire est monté le temps du `RUN`, puis retiré. Seul ce que
l'étape écrit ailleurs (ici `/resultat`) entre dans la couche.

## 🔗 Exercice 2 : partager un cache par son identifiant

Un cache monté est désigné par son `id`, pas par son chemin. Deux Dockerfile
différents, qui le montent à deux endroits différents, voient donc le même
contenu. Le premier y dépose un fichier, le second le lit :

```bash
cat > Dockerfile.ecrit <<EOF
FROM $ALPINE
RUN --mount=type=cache,id=essai-partage,target=/depot \
    echo "paquet-1.0" > /depot/paquet.txt
EOF
cat > Dockerfile.lit <<EOF
FROM $ALPINE
RUN --mount=type=cache,id=essai-partage,target=/ailleurs \
    cat /ailleurs/paquet.txt > /trouve
EOF
docker build -q -t essai-montage:ecrit -f Dockerfile.ecrit . >/dev/null
docker build -q -t essai-montage:lit -f Dockerfile.lit . >/dev/null
docker run --rm essai-montage:lit cat /trouve
```

```text
paquet-1.0
```

Le second build a lu, sous `/ailleurs`, le fichier écrit par le premier sous
`/depot`. Sans `id`, le cache prend le chemin `target` comme identifiant : deux
projets qui montent tous deux `/root/.cache/pip` partagent alors leur cache
sans l'avoir décidé.

## 🧹 Exercice 3 : ce qui vide le cache monté

Reprenez le Dockerfile de l'exercice 1. Construisez un quatrième tour, videz
le cache de construction, construisez un cinquième tour, puis un sixième avec
`--no-cache` :

```bash
docker build -q -t essai-montage:passages -f Dockerfile.passages --build-arg TOUR=4 . >/dev/null
docker run --rm essai-montage:passages cat /resultat
docker builder prune -f | tail -1
docker build -q -t essai-montage:passages -f Dockerfile.passages --build-arg TOUR=5 . >/dev/null
docker run --rm essai-montage:passages cat /resultat
docker build -q --no-cache -t essai-montage:passages -f Dockerfile.passages --build-arg TOUR=6 . >/dev/null
docker run --rm essai-montage:passages cat /resultat
```

```text
passages=4
Total:	82.49kB
passages=1
passages=1
```

Le quatrième tour trouve les trois lignes précédentes. Après
`docker builder prune`, le compte repart à 1 : le cache monté fait partie du
cache de construction, et le nettoyage le supprime. Avec `--no-cache`, il
repart aussi à 1, alors que rien n'a été nettoyé : l'option ignore le cache
monté en même temps que les couches. Un Dockerfile doit donc fonctionner avec
un cache monté vide.

## 🧹 Nettoyage

Supprimez les images et le répertoire d'essai, puis les caches montés que le
cours a créés (`--filter type=exec.cachemount` ne vise qu'eux). La dernière
commande compte les images `essai-*` qui restent :

```bash
cd ~
docker rmi essai-montage:passages essai-montage:ecrit essai-montage:lit | grep -c Untagged
rm -rf ~/essai-montage
docker builder prune -f --filter type=exec.cachemount | tail -1
docker images --format '{{.Repository}}' | grep -c '^essai-'
```

```text
3
Total:	8.192kB
0
```

Plus rien de ce cours. Quittez ensuite la machine et remettez le lab à zéro.
`dsoxlab reset` rejoue le nettoyage puis la préparation du lab : vous
retrouvez exactement l'état de départ du challenge. Il vous demande de
confirmer : répondez `y`.

```bash
exit
dsoxlab reset buildkit-cache-monte
dsoxlab check buildkit-cache-monte
```

```text
╭─ Résultat : buildkit-cache-monte ─╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge vous attend, intact.

## 🎯 Le challenge

À vous, seul cette fois : faire réutiliser une dépendance par une étape qui se
rejoue à chaque changement de source, sans que le cache entre dans l'image.

```bash
dsoxlab run buildkit-cache-monte
dsoxlab challenge buildkit-cache-monte
```
