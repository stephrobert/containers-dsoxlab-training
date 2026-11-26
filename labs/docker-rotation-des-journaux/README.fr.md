# Faire tourner le journal d'un conteneur

La leçon règle la rotation et mesure les fichiers. Ce cours regarde ce qui
reste dans un journal borné : ce que l'on peut encore lire, des options
refusées, un autre pilote, la compression, et une ligne trop longue.

Vous travaillez dans `~/essai-journal`, sur des conteneurs `essai-*`. Le
challenge porte sur `dsoxlab-log-rotation` : n'y touchez pas pendant le cours.

Page associée : [Faire tourner les journaux, et reprendre du disque](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/journaux-et-espace-disque/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run docker-rotation-des-journaux
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. La fonction `bavard`
lance un conteneur qui écrit 4 000 lignes, `fichiers` liste ses journaux.
**Gardez le même terminal jusqu'au nettoyage** : les variables n'existent que
dans lui.

```bash
mkdir -p ~/essai-journal && cd ~/essai-journal
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
bavard() { docker run -d --init --name "essai-$1" "${@:2}" "$IMAGE" sh -c 'for i in $(seq 1 4000); do echo "ligne $i"; done; sleep 600' > /dev/null; sleep 2; }
fichiers() { sudo sh -c "ls -l $(dirname "$(docker inspect "essai-$1" --format '{{.LogPath}}')")" | awk '/json.log/{print $5, $9}' | sed 's/[0-9a-f]\{64\}/ID/'; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 📏 Exercice 1 : ce que l'on peut encore lire

Bornez le journal, puis comptez les lignes et les octets qui restent :

```bash
bavard borne --log-opt max-size=20k --log-opt max-file=2
docker logs essai-borne | wc -l
docker logs essai-borne | sed -n '1p;$p'
fichiers borne
```

```text
267
ligne 3734
ligne 4000
1537 ID-json.log
20059 ID-json.log.1
```

Le fichier en cours vient de repartir presque vide, l'autre est plein : selon
le moment, il reste entre un et deux fichiers de lignes. Prévoyez la taille sur
le cas le plus court.

## 🚫 Exercice 2 : des options refusées

Trompez-vous de quatre façons, dont une que Docker accepte :

```bash
docker run --rm --log-opt max-siz=10k "$IMAGE" true 2>&1 | grep -o "unknown log opt 'max-siz'"
docker run --rm --log-opt max-size=10x "$IMAGE" true 2>&1 | grep -o "invalid suffix.*"
docker run --rm --log-opt max-size=0 "$IMAGE" true 2>&1 | grep -o "max-size must be.*"
docker run --rm --log-opt max-file=2 "$IMAGE" echo accepte
docker update --log-opt max-size=1k essai-borne 2>&1 | grep -o 'unknown flag: --log-opt'
```

```text
unknown log opt 'max-siz'
invalid suffix: 'x'
max-size must be a positive number
accepte
unknown flag: --log-opt
```

`max-file` sans `max-size` est accepté et ne borne rien : aucun fichier
n'atteint jamais sa taille. Et un journal ne se règle pas après coup : il faut
recréer le conteneur.

## 📦 Exercice 3 : un autre pilote

Gardez les mêmes bornes avec le pilote `local` :

```bash
bavard local --log-driver local --log-opt max-size=20k --log-opt max-file=2
docker logs essai-local | wc -l
docker inspect essai-local --format '[{{.LogPath}}]'
```

```text
809
[]
```

Le même budget retient plus de lignes, parce que le format est plus compact.
`LogPath` est vide : un outil qui lit les fichiers JSON ne trouvera plus rien.
`docker logs` continue de marcher.

## 🗜️ Exercice 4 : la compression

Compressez les fichiers tournés, et comptez ce qui reste lisible :

```bash
bavard compresse --log-opt max-size=20k --log-opt max-file=5 --log-opt compress=true
fichiers compresse | grep -c gz
docker logs essai-compresse | wc -l
docker restart --timeout 1 essai-compresse > /dev/null; sleep 2
docker logs --tail 1 essai-compresse
```

```text
4
1011
ligne 4000
```

`docker logs` relit les fichiers compressés sans rien demander. Un redémarrage
ne vide pas le journal : il continue dans les mêmes fichiers.

## 🧵 Exercice 5 : une ligne trop longue

Écrivez une seule ligne de 60 000 caractères, et comptez les enregistrements :

```bash
docker run -d --init --name essai-longue "$IMAGE" sh -c 'head -c 60000 /dev/zero | tr "\0" a; echo; sleep 600' > /dev/null; sleep 1
docker logs essai-longue | wc -l
sudo cat "$(docker inspect essai-longue --format '{{.LogPath}}')" | wc -l
```

```text
1
4
```

Docker découpe une ligne longue en enregistrements de 16 Kio. `docker logs` la
recolle, mais un outil qui lit le fichier voit quatre morceaux, dont les
premiers ne sont pas des lignes complètes : un message JSON long y devient
illisible.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-borne essai-local essai-compresse essai-longue > /dev/null
rm -rf ~/essai-journal
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
dsoxlab reset docker-rotation-des-journaux
dsoxlab check docker-rotation-des-journaux
```

```text
╭─ Résultat : docker-rotation-des-journaux ─╮
│  0 / 100 pts                              │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests          │
╰───────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un service bavard, un seul, à contenir sans toucher
aux autres.

```bash
dsoxlab run docker-rotation-des-journaux
dsoxlab challenge docker-rotation-des-journaux
```
