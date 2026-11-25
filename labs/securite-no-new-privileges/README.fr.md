# Empêcher les gains de privilèges au runtime

La leçon pose le drapeau et vérifie qu'il est hérité. Ce cours le met à
l'épreuve d'un vrai programme setuid, puis montre l'inventaire de ces
programmes, les écritures de l'option, les entrées par `docker exec`, et un
programme setuid qui arrive par un volume.

Vous travaillez dans `~/essai-gain`, sur l'image `essai-gain`. Elle contient
`lit`, une copie setuid d'un outil qui affiche un fichier. Le challenge porte
sur le `worker` de son projet : n'y touchez pas pendant le cours.

Page associée : [Durcir le runtime : capabilities et privilèges](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/securite/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run securite-no-new-privileges
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `J` lance un conteneur
sous l'UID 1000. **Gardez le même terminal jusqu'au nettoyage** : les variables
n'existent que dans lui.

```bash
mkdir -p ~/essai-gain && cd ~/essai-gain
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cat > Dockerfile <<'EOF'
ARG IMAGE
FROM $IMAGE
RUN cp /usr/bin/iconv /usr/local/bin/lit && chmod 4755 /usr/local/bin/lit
RUN cp /usr/bin/iconv /usr/local/bin/lit-g && chgrp shadow /usr/local/bin/lit-g && chmod 2755 /usr/local/bin/lit-g
EOF
docker build -q --build-arg IMAGE="$IMAGE" -t essai-gain . > /dev/null
J="docker run --rm --network none --user 1000:1000"
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🔓 Exercice 1 : un vrai gain de privilège

Lisez un fichier réservé, avec `cat`, puis avec les deux copies :

```bash
$J essai-gain ls -l /etc/shadow | cut -c1-34
$J essai-gain head -c 5 /etc/shadow
$J essai-gain sh -c 'lit /etc/shadow | head -1'
$J essai-gain sh -c 'lit-g /etc/shadow | head -1'
$J --security-opt no-new-privileges essai-gain lit /etc/shadow
$J --security-opt no-new-privileges essai-gain lit-g /etc/shadow
```

```text
-rw-r-----    1 root     shadow
head: /etc/shadow: Permission denied
root:*::0:::::
root:*::0:::::
iconv: /etc/shadow: Permission denied
iconv: /etc/shadow: Permission denied
```

Le conteneur démarre sous l'UID 1000 et lit pourtant le fichier. Le bit setuid
prête le compte du propriétaire, le bit setgid prête son groupe : les deux
comptent. Le drapeau ferme les deux.

## 🔍 Exercice 2 : l'inventaire d'une image

Cherchez les programmes setuid et setgid d'une image, et regardez ce que donne
le retrait des capabilities :

```bash
docker run --rm essai-gain find / -xdev -perm /6000 -type f | sort
docker run --rm "$IMAGE" find / -xdev -perm /6000 -type f | wc -l
$J --cap-drop ALL essai-gain sh -c 'lit /etc/shadow | head -1'
$J --cap-drop ALL essai-gain grep CapBnd /proc/1/status
```

```text
/usr/local/bin/lit
/usr/local/bin/lit-g
0
root:*::0:::::
CapBnd:	0000000000000000
```

Retirer toutes les capabilities n'a pas suffi : `lit` devient root sans pouvoir
spécial, mais root possède le fichier. Les deux réglages se complètent. Et un
programme setuid qui n'est pas dans l'image n'a pas besoin d'être bloqué :
faites cet inventaire à la construction.

## ✍️ Exercice 3 : les écritures de l'option

Essayez six écritures et lisez le drapeau à chaque fois :

```bash
for o in no-new-privileges no-new-privileges:true no-new-privileges=true no-new-privileges:false no-new-privilege no-new-privileges:oui; do
  echo "$o -> $($J --security-opt "$o" essai-gain grep NoNewPrivs /proc/1/status 2>&1 | grep -oE 'NoNewPrivs.*|invalid --security-opt' | tr '\t' ' ')"
done
docker create --name essai-ecrit --security-opt no-new-privileges:false essai-gain true > /dev/null
docker inspect essai-ecrit --format '{{json .HostConfig.SecurityOpt}}'
docker rm essai-ecrit > /dev/null
```

```text
no-new-privileges -> NoNewPrivs: 1
no-new-privileges:true -> NoNewPrivs: 1
no-new-privileges=true -> NoNewPrivs: 1
no-new-privileges:false -> NoNewPrivs: 0
no-new-privilege -> invalid --security-opt
no-new-privileges:oui -> invalid --security-opt
["no-new-privileges:false"]
```

Une faute est refusée, mais `:false` est accepté et ne protège rien. Dans une
revue, chercher le mot `no-new-privileges` ne suffit donc pas. La preuve est
`NoNewPrivs` dans `/proc/1/status`.

## 🚪 Exercice 4 : les entrées par docker exec

Entrez dans un conteneur protégé de trois façons :

```bash
docker run -d --init --name essai-entree --user 1000:1000 --security-opt no-new-privileges essai-gain sleep 600 > /dev/null
docker exec essai-entree lit /etc/shadow
docker exec --privileged essai-entree lit /etc/shadow
docker exec --user 0 essai-entree head -c 5 /etc/shadow; echo
docker rm -f essai-entree > /dev/null
docker run --rm --security-opt no-new-privileges "$IMAGE" su nobody -s /bin/sh -c 'id -u'
```

```text
iconv: /etc/shadow: Permission denied
iconv: /etc/shadow: Permission denied
root:
65534
```

Le drapeau s'applique à tous les processus ajoutés, même avec `--privileged`.
Il n'empêche pas d'entrer directement en root avec `--user 0` : ce n'est pas un
gain, c'est une identité donnée au départ. Et perdre des droits, comme ce root
qui devient `nobody`, reste permis.

## 📦 Exercice 5 : un setuid qui arrive par un volume

Déposez la copie setuid dans un volume, puis montez-le dans un conteneur dont
l'image n'en a aucune :

```bash
docker volume create essai-depot > /dev/null
docker run --rm -v essai-depot:/depot essai-gain sh -c 'cp /usr/local/bin/lit /depot/ && chmod 4755 /depot/lit'
$J -v essai-depot:/depot "$IMAGE" sh -c '/depot/lit /etc/shadow | head -1'
$J -v essai-depot:/depot --security-opt no-new-privileges "$IMAGE" /depot/lit /etc/shadow
docker run --rm --tmpfs /espace "$IMAGE" mount | grep -oE '/espace type tmpfs \(rw,nosuid'
docker volume rm essai-depot
```

```text
root:*::0:::::
iconv: /etc/shadow: Permission denied
/espace type tmpfs (rw,nosuid
essai-depot
```

L'inventaire de l'image n'aurait rien vu : le programme est venu avec les
données. Un tmpfs est monté en `nosuid`, un volume ne l'est pas. C'est pourquoi
le drapeau reste utile sur une image propre.

## 🧹 Nettoyage

```bash
cd ~
docker rmi -f essai-gain > /dev/null
rm -rf ~/essai-gain
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
dsoxlab reset securite-no-new-privileges
dsoxlab check securite-no-new-privileges
```

```text
╭─ Résultat : securite-no-new-privileges ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests        │
╰─────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un programme setuid à garder, et un gain à rendre
impossible.

```bash
dsoxlab run securite-no-new-privileges
dsoxlab challenge securite-no-new-privileges
```
