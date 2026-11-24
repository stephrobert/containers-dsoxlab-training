# Sauvegarder une stack Compose, et la restaurer ailleurs

La leçon sauvegarde une base, un volume et une configuration, puis les
restaure. Ce cours montre cinq sauvegardes qui ont l'air bonnes : un échec
caché par un tube, des fichiers oubliés, une archive coupée, une restauration
qui change les propriétaires, et une base dont les rôles manquent.

Vous travaillez dans `~/essai-coffre`, sur des volumes et des conteneurs
`essai-*`. Le challenge porte sur la stack `herbier` : n'y touchez pas pendant
le cours.

Page associée : [Sauvegarder et restaurer une application](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/sauvegarder-et-restaurer/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-sauver-et-restaurer
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
Remplissez un volume. **Gardez le même terminal jusqu'au nettoyage** : les
variables n'existent que dans lui.

```bash
mkdir -p ~/essai-coffre && cd ~/essai-coffre
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
PG=postgres:18.6-alpine3.24@sha256:10a5c69a83035ab5239f5620d708520e8b28f5aa1f2b20143e6024532edadfb5
docker volume create essai-source > /dev/null
docker run --rm -v essai-source:/v "$IMAGE" sh -c 'head -c 300000 /dev/urandom > /v/planche; echo prive > /v/note; chown 4242:4242 /v/note; chmod 600 /v/note; touch /v/.reglage'
```

```text
5.6.1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🚰 Exercice 1 : un échec caché par un tube

Archivez un répertoire qui n'existe pas, à travers un tube, sans puis avec
`pipefail` :

```bash
docker run --rm -v essai-source:/v:ro "$IMAGE" tar cz -C /v absent 2> /dev/null | cat > vide.tgz; echo "code: $?"
set -o pipefail
docker run --rm -v essai-source:/v:ro "$IMAGE" tar cz -C /v absent 2> /dev/null | cat > vide.tgz; echo "code: $?"
set +o pipefail
tar tzf vide.tgz | wc -l
```

```text
code: 0
code: 1
0
```

Le code d'un tube est celui de sa dernière commande : `cat` a réussi, et le
fichier existe, vide de tout contenu. `set -o pipefail` rend l'échec visible.
Mettez-le en tête de vos scripts de sauvegarde.

## 🙈 Exercice 2 : des fichiers oubliés

Archivez avec `*`, puis avec `.` :

```bash
docker run --rm -v essai-source:/v:ro "$IMAGE" sh -c 'cd /v && tar cz *' > etoile.tgz
tar tzf etoile.tgz | sort
echo '--'
(umask 077; docker run --rm -v essai-source:/v:ro "$IMAGE" tar cz -C /v . > complet.tgz)
tar tzf complet.tgz | sort
stat -c '%a %n' etoile.tgz complet.tgz
```

```text
note
planche
--
./
./.reglage
./note
./planche
664 etoile.tgz
600 complet.tgz
```

Le shell n'inclut pas les fichiers cachés dans `*` : `.reglage` manque, sans
erreur. `-C /v .` prend tout le répertoire. L'`umask` posé dans le sous-shell
garde aussi l'archive privée.

## 🪓 Exercice 3 : une archive coupée

Coupez l'archive, comme le ferait un disque plein, puis faites de même avec une
sauvegarde de base :

```bash
head -c 200000 complet.tgz > coupe.tgz
gzip -t coupe.tgz 2>&1 | grep -o 'unexpected end of file'
docker run -d --name essai-base -e POSTGRES_PASSWORD=demo "$PG" > /dev/null
until docker exec essai-base psql -U postgres -h 127.0.0.1 -c 'select 1' > /dev/null 2>&1; do sleep 1; done
docker exec essai-base psql -U postgres -q -c 'create table t as select i, md5(i::text) from generate_series(1,20000) i'
docker exec essai-base pg_dump -U postgres -Fc postgres > complet.dump
head -c 100000 complet.dump > coupe.dump
docker exec -i essai-base pg_restore --list < coupe.dump | grep -c 'TABLE DATA'
docker exec -i essai-base pg_restore -f /dev/null < coupe.dump > /dev/null 2>&1; echo "coupe: $?"
docker exec -i essai-base pg_restore -f /dev/null < complet.dump; echo "complet: $?"
```

```text
unexpected end of file
1
coupe: 1
complet: 0
```

`gzip -t` voit la coupure. `pg_restore --list` ne la voit pas : la table des
matières est au début du fichier, et elle est intacte. Faire lire l'archive
entière, avec `-f /dev/null`, la révèle sans rien restaurer.

## 👤 Exercice 4 : une restauration qui change les propriétaires

Restaurez dans un volume déjà occupé, puis dans un volume neuf sans être root :

```bash
docker volume create essai-occupe > /dev/null
docker run --rm -v essai-occupe:/v "$IMAGE" touch /v/ancien
docker run --rm -i -v essai-occupe:/v "$IMAGE" tar xz -C /v < complet.tgz
docker run --rm -v essai-occupe:/v "$IMAGE" sh -c 'ls -A /v; stat -c "%u:%g" /v/note'
docker volume create essai-simple > /dev/null
docker run --rm -v essai-simple:/v "$IMAGE" chown 1001 /v
docker run --rm -i --user 1001 -v essai-simple:/v "$IMAGE" tar xz -C /v < complet.tgz; echo "code: $?"
docker run --rm -v essai-simple:/v "$IMAGE" stat -c '%u:%g' /v/note
```

```text
.reglage
ancien
note
planche
4242:4242
code: 0
1001:0
```

`tar` ajoute sans effacer : `ancien` est mêlé aux fichiers restaurés. Restaurez
dans un volume vide. Sans root, l'extraction réussit aussi, mais `note`
n'appartient plus à 4242 : l'application d'origine ne pourra plus la lire.

## 🎭 Exercice 5 : une base sans ses rôles

Donnez un droit à un rôle, sauvegardez, puis restaurez dans un serveur neuf :

```bash
docker exec essai-base psql -U postgres -q -c 'create role lecteur' -c 'grant select on t to lecteur'
docker exec essai-base pg_dump -U postgres -Fc postgres > droits.dump
docker run -d --name essai-cible -e POSTGRES_PASSWORD=demo "$PG" > /dev/null
until docker exec essai-cible psql -U postgres -h 127.0.0.1 -c 'select 1' > /dev/null 2>&1; do sleep 1; done
docker exec -i essai-cible pg_restore -U postgres -d postgres < droits.dump 2>&1 | grep -o 'role "lecteur" does not exist'
docker exec essai-cible psql -U postgres -Atc 'select count(*) from t'
docker exec essai-base pg_dumpall -U postgres --roles-only | grep 'CREATE ROLE lecteur'
```

```text
role "lecteur" does not exist
20000
CREATE ROLE lecteur;
```

Les 20 000 lignes sont là, mais le droit n'a pas pu être rendu : `pg_dump` ne
sauvegarde pas les rôles, qui appartiennent au serveur. `pg_dumpall
--roles-only` les donne. Cette sortie contient les empreintes des mots de passe
: protégez-la comme le reste.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f -v essai-base essai-cible > /dev/null
docker volume rm essai-source essai-occupe essai-simple > /dev/null
rm -r ~/essai-coffre
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker network ls --format '{{.Name}}' | grep -c '^essai-'
docker volume ls --format '{{.Name}}' | grep -c '^essai-'
```

```text
0
0
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset compose-sauver-et-restaurer
dsoxlab check compose-sauver-et-restaurer
```

```text
╭─ Résultat : compose-sauver-et-restaurer ─╮
│  0 / 100 pts                             │
│  ░░░░░░░░░░░░░░░░░░░░  0/5 tests         │
╰──────────────────────────────────────────╯
```

0 sur 5 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un herbier en service, à remonter ailleurs sans y
toucher.

```bash
dsoxlab run compose-sauver-et-restaurer
dsoxlab challenge compose-sauver-et-restaurer
```
