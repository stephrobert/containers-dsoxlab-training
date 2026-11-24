# Deux conteneurs, un volume, des droits qui tiennent

La leçon aligne un groupe partagé, montre le setgid et le masque de création.
Ce cours ajoute cinq gestes : un numéro qui change de nom, un compte absent, un
groupe absent, la suppression du fichier d'un autre, et le propriétaire d'un
fichier copié.

Vous travaillez dans `~/essai-droits`, sur le volume `essai-commun` et des
conteneurs `essai-*`. Le challenge porte sur `rapport`, `verificateur` et
`rapports-partages` : n'y touchez pas pendant le cours.

Page associée : [Droits sur un volume Docker : trois causes courantes d'un accès refusé](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/droits-sur-un-volume/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run donnees-permissions-uid-gid
```

Vous êtes connecté à `docker.lab`, où le moteur tourne, et l'image d'Alpine est
sur la machine. **Gardez le même terminal jusqu'au nettoyage** : les variables
n'existent que dans lui.

```bash
mkdir -p ~/essai-droits && cd ~/essai-droits
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🏷️ Exercice 1 : un numéro, deux noms

Créez un fichier dans un conteneur sous un compte qui porte le même numéro que
le vôtre :

```bash
id -un
docker run --rm -v "$PWD:/d" "$IMAGE" sh -c "adduser -D -u $(id -u) paul; su paul -c 'touch /d/note'; ls -l /d/note | awk '{print \$3}'"
ls -l note | awk '{print $3}'
ls -ln note | awk '{print $3}'
```

```text
ansible
paul
ansible
1001
```

Le conteneur affiche `paul`, l'hôte affiche votre compte, et c'est le même
fichier. Seul le numéro est enregistré : chaque système le traduit avec son
propre fichier de comptes. Pour comparer des droits, lisez les numéros.

## 👤 Exercice 2 : un compte absent de l'image

Demandez un compte par son nom, puis par un numéro que l'image ne connaît pas :

```bash
docker run --rm --user paul "$IMAGE" id 2>&1 | grep -o 'unable to find user.*'
docker run --rm --user 4343 "$IMAGE" id
```

```text
unable to find user paul: no matching entries in passwd file
uid=4343 gid=0(root) groups=0(root)
```

Un nom se cherche dans l'image : absent, il empêche le conteneur de démarrer.
Un numéro est toujours accepté. Un compte demandé par son nom signale donc une
erreur que le numéro laisserait passer.

## 👥 Exercice 3 : un groupe absent de l'image

Même essai avec un groupe supplémentaire :

```bash
docker run --rm --user 4343 --group-add equipage "$IMAGE" id 2>&1 | grep -io 'unable to find group.*'
docker run --rm --user 4343 --group-add 5151 "$IMAGE" id
```

```text
unable to find group equipage: no matching entries in group file
uid=4343 gid=0(root) groups=0(root),5151
```

`--group-add` suit la même règle. Le numéro 5151 apparaît dans `groups`, à côté
du groupe principal, resté à 0 (root) : `--user 4343` n'a fixé que
l'utilisateur.

## 🗑️ Exercice 4 : supprimer le fichier d'un autre

Deux comptes écrivent dans un répertoire ouvert à tous, comme `/tmp`. Le second
supprime le fichier du premier, puis recommence avec le bit collant (`t`) :

```bash
commun() { docker run --rm --user "$1" -v essai-commun:/c "$IMAGE" sh -c "$2"; }
commun 0:0 'chmod 777 /c'
commun 4343:5151 'echo a > /c/premier'
commun 4444:5151 'rm -f /c/premier && echo supprime'
commun 0:0 'chmod 1777 /c; stat -c %A /c'
commun 4343:5151 'echo a > /c/premier'
commun 4444:5151 'rm -f /c/premier'; echo "code: $?"
```

```text
supprime
drwxrwxrwt
rm: can't remove '/c/premier': Operation not permitted
code: 1
```

Supprimer un fichier demande le droit d'écrire dans le répertoire, pas dans le
fichier. Le bit collant restreint la suppression au propriétaire du fichier et
à celui du répertoire. C'est le réglage de `/tmp`.

## 📥 Exercice 5 : le propriétaire d'un fichier copié

Copiez un fichier de l'hôte dans un conteneur non root, sans puis avec l'option
`-a` :

```bash
echo reglage > conf.txt
docker run -d --name essai-cible --user 4343 "$IMAGE" sleep 600 > /dev/null
docker cp -q conf.txt essai-cible:/tmp/sans
docker cp -q -a conf.txt essai-cible:/tmp/avec
docker exec essai-cible stat -c '%u:%g %n' /tmp/sans /tmp/avec
docker exec essai-cible sh -c 'echo x >> /tmp/sans'
```

```text
1001:1001 /tmp/sans
4343:0 /tmp/avec
sh: can't create /tmp/sans: Permission denied
```

Sans option, le fichier garde les numéros de l'hôte : l'application peut le
lire, pas le modifier. Avec `-a`, il est donné à l'utilisateur du conteneur,
4343, et à son groupe principal, 0. Contrôlez toujours le propriétaire après
une copie.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-cible > /dev/null
docker volume rm essai-commun
rm -r ~/essai-droits
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-commun
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset donnees-permissions-uid-gid
dsoxlab check donnees-permissions-uid-gid
```

```text
╭─ Résultat : donnees-permissions-uid-gid ─╮
│  0 / 100 pts                             │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests         │
╰──────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : deux identités différentes écrivent dans un volume
qui n'est pas ouvert à tous.

```bash
dsoxlab run donnees-permissions-uid-gid
dsoxlab challenge donnees-permissions-uid-gid
```
