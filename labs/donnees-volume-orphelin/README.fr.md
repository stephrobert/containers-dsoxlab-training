# Récupérer les données orphelines et retirer seulement le jetable

La leçon retrouve un volume, le sauvegarde et retire le bon. Ce cours montre
les erreurs qui abîment ou masquent des données : une étiquette que l'on croit
changée, un volume tenu par un conteneur arrêté, un volume rempli par une
image, une copie infidèle, et un nom mal tapé.

Vous travaillez sur des volumes `essai-*`. Le challenge porte sur deux volumes
`dsoxlab-donnees-volume-orphelin-*` : n'y touchez pas pendant le cours.

Page associée : [Retrouver des données orphelines sans tout effacer](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/donnees-orphelines/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run donnees-volume-orphelin
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-volumes && cd ~/essai-volumes
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🏷️ Exercice 1 : une étiquette que l'on croit changée

Créez un volume avec une étiquette, puis recréez-le avec une autre valeur :

```bash
docker volume create --label equipe=paie essai-a
docker volume create --label equipe=rh essai-a; echo "code: $?"
docker volume inspect essai-a --format '{{.Labels}}'
docker volume ls -q --filter label=equipe=rh | wc -l
```

```text
essai-a
essai-a
code: 0
map[equipe:paie]
0
```

La seconde création réussit et ne change rien : le volume existait. Une
étiquette se lit dans `inspect`, jamais dans la commande qu'on a tapée. Un
nettoyage filtré sur `equipe=rh` ne verrait pas ce volume.

## ⚓ Exercice 2 : un volume tenu par un conteneur arrêté

Attachez le volume à un conteneur qui ne tourne pas, puis cherchez les
orphelins :

```bash
docker create --name essai-arrete -v essai-a:/d "$IMAGE" true > /dev/null
docker volume ls -q --filter dangling=true | grep -c '^essai-a$'
docker volume rm essai-a 2>&1 | grep -o 'volume is in use'
docker ps -a --filter volume=essai-a --format '{{.Names}} {{.State}}'
docker rm -v essai-arrete > /dev/null
docker volume ls -q --filter dangling=true | grep -c '^essai-a$'
```

```text
0
volume is in use
essai-arrete created
1
```

Un conteneur créé ou arrêté compte comme une référence. `docker ps -a --filter
volume=` dit qui tient le volume. Et `docker rm -v` ne retire que les volumes
sans nom : celui-ci devient orphelin.

## 🫗 Exercice 3 : un volume rempli par une image

Montez un volume vide sur un dossier garni de l'image, en écriture, en lecture
seule, puis avec `nocopy` :

```bash
compte() { docker run --rm -v "$1:/d:ro" "$IMAGE" sh -c 'ls -A /d | wc -l'; }
for m in rw ro nocopy; do
  docker volume create essai-$m > /dev/null
  docker run --rm -v essai-$m:/etc/apk:$m "$IMAGE" true
  echo "$m : $(compte essai-$m) fichiers"
done
```

```text
rw : 5 fichiers
ro : 5 fichiers
nocopy : 0 fichiers
```

Docker copie le contenu de l'image dans un volume vide, **même monté en lecture
seule**. Pour examiner un volume que l'on croit vide, montez-le sur un dossier
qui n'existe pas dans l'image, ou ajoutez `nocopy`.

## 🧬 Exercice 4 : une copie infidèle

Copiez un volume de deux façons, et comparez le propriétaire puis le contenu :

```bash
docker run --rm -v essai-a:/d "$IMAGE" sh -c 'mkdir /d/x; echo recu > /d/x/f; chown -R 1234:1234 /d/x'
docker volume create essai-b > /dev/null
C="docker run --rm -v essai-a:/s:ro -v essai-b:/d $IMAGE"
$C cp -r /s/. /d/
$C stat -c '%u' /d/x/f
$C cp -a /s/. /d/
$C stat -c '%u' /d/x/f
$C sh -c 'cd /s && find . -type f -exec sha256sum {} + > /tmp/s; cd /d && sha256sum -c /tmp/s'
```

```text
0
1234
./x/f: OK
```

`cp -r` donne tout à root, et un service non root ne lirait plus ses données.
`cp -a` garde propriétaires, droits et dates. La dernière ligne compare les
contenus : c'est elle qui autorise à parler de copie.

## 🔤 Exercice 5 : un nom mal tapé

Montez un volume dont le nom a une lettre de trop, puis un sous-dossier qui
n'existe pas :

```bash
docker run --rm -v essai-aa:/d "$IMAGE" sh -c 'ls -A /d | wc -l'
docker volume ls -q | grep '^essai-a'
docker run --rm --mount type=volume,src=essai-a,dst=/d,volume-subpath=x "$IMAGE" ls /d
docker run --rm --mount type=volume,src=essai-a,dst=/d,volume-subpath=y "$IMAGE" ls /d 2>&1 | grep -o 'no such file or directory'
```

```text
0
essai-a
essai-aa
f
no such file or directory
```

Le nom inconnu crée un volume vide, sans un mot : le service démarre, et ses
données semblent perdues. Le sous-dossier inconnu, lui, arrête le lancement.
Devant des données absentes, vérifiez d'abord le nom monté.

## 🧹 Nettoyage

```bash
cd ~
docker volume rm essai-a essai-aa essai-b essai-rw essai-ro essai-nocopy > /dev/null
rm -rf ~/essai-volumes
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
dsoxlab reset donnees-volume-orphelin
dsoxlab check donnees-volume-orphelin
```

```text
╭─ Résultat : donnees-volume-orphelin ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests     │
╰──────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : des données à reconnecter, et un seul volume à
retirer.

```bash
dsoxlab run donnees-volume-orphelin
dsoxlab challenge donnees-volume-orphelin
```
