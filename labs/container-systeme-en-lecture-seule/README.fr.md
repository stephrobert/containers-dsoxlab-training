# Utiliser une racine de conteneur en lecture seule

La leçon recense les écritures d'un service, fige sa racine et borne ses tmpfs.
Ce cours regarde ce que la lecture seule laisse passer et ce qu'elle casse sans
le dire : des emplacements encore inscriptibles, un `noexec` contourné, un
tmpfs qui cache des fichiers, un tmpfs plein de fichiers vides, et une écriture
perdue en silence.

Vous travaillez sur des conteneurs `essai-*`. Le challenge porte sur le
`worker` de son projet : n'y touchez pas pendant le cours.

Page associée : [Racine en lecture seule, et arrêt sans perte](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/racine-en-lecture-seule/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run container-systeme-en-lecture-seule
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-fige && cd ~/essai-fige
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
docker run -d --init --name essai-fige --read-only "$IMAGE" sleep 600 > /dev/null
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🗺️ Exercice 1 : ce qui reste inscriptible

Essayez d'écrire dans sept dossiers, puis dans trois fichiers que Docker
prépare :

```bash
docker exec essai-fige sh -c 'for d in / /tmp /etc /sys /proc/sys/kernel /dev /dev/shm; do (echo x > $d/essai) 2>/dev/null && echo "$d : oui" || echo "$d : non"; done'
docker exec essai-fige sh -c 'for f in /etc/hosts /etc/resolv.conf /etc/hostname; do (echo "#" >> $f) 2>/dev/null && echo "$f : oui" || echo "$f : non"; done'
docker exec essai-fige sh -c 'mount' | grep -oE '/dev/shm type tmpfs .*size=[0-9]+k'
```

```text
/ : non
/tmp : non
/etc : non
/sys : non
/proc/sys/kernel : non
/dev : oui
/dev/shm : oui
/etc/hosts : non
/etc/resolv.conf : non
/etc/hostname : non
/dev/shm type tmpfs (rw,nosuid,nodev,noexec,relatime,size=65536k
```

`/dev` et `/dev/shm` restent ouverts sans que vous ayez rien déclaré.
`/dev/shm` offre 64 Mio, pris sur la mémoire du conteneur. Les trois fichiers
de réseau, eux, sont figés aussi : un programme qui réécrit `/etc/hosts`
échouera.

## 📥 Exercice 2 : des outils qui refusent aussi

Copiez un fichier avec `docker cp`, puis essayez de remonter la racine en
écriture :

```bash
echo bonjour > note
docker cp -q note essai-fige:/dev/shm/note
docker exec essai-fige mount -o remount,rw / 2>&1
docker exec essai-fige touch /preuve
docker exec -i essai-fige sh -c 'cat > /dev/shm/note' < note; echo "code: $?"
```

```text
Error response from daemon: container rootfs is marked read-only
mount: permission denied (are you root?)
touch: /preuve: Read-only file system
code: 0
```

`docker cp` refuse tout, même vers un dossier inscriptible. Pour déposer un
fichier dans un conteneur figé, passez par son entrée, comme la dernière ligne,
ou par un montage prévu à la création.

## 🎭 Exercice 3 : un noexec contourné

Déposez un script et un binaire dans un tmpfs en `noexec` :

```bash
docker run --rm --read-only --tmpfs /espace:size=2m,noexec "$IMAGE" sh -c '
printf "echo execute\n" > /espace/s; chmod +x /espace/s; cp /bin/busybox /espace/b
/espace/s; echo "script direct: $?"
sh /espace/s; echo "par sh: $?"
/espace/b true; echo "binaire: $?"'
```

```text
sh: /espace/s: Permission denied
script direct: 126
execute
par sh: 0
sh: /espace/b: Permission denied
binaire: 126
```

Le binaire et le script sont refusés, mais `sh` lit le script et l'exécute.
`noexec` gêne un binaire déposé ; il ne protège pas d'un interpréteur présent
dans l'image. Une image sans shell ferme cette porte.

## 🫥 Exercice 4 : un tmpfs qui cache des fichiers

Comptez les fichiers d'un dossier de l'image, puis montez dessus un tmpfs, puis
un volume :

```bash
docker run --rm "$IMAGE" sh -c 'ls -A /etc/apk | wc -l'
docker run --rm --read-only --tmpfs /etc/apk "$IMAGE" sh -c 'ls -A /etc/apk | wc -l'
docker volume create essai-copie > /dev/null
docker run --rm --read-only -v essai-copie:/etc/apk "$IMAGE" sh -c 'ls -A /etc/apk | wc -l; touch /etc/apk/neuf && echo inscriptible'
docker volume rm essai-copie
```

```text
5
0
5
inscriptible
essai-copie
```

Le tmpfs recouvre le dossier et le montre vide. Un volume vide, lui, reçoit
d'abord une copie du contenu de l'image. Montez un tmpfs sur un dossier vide,
ou prévoyez que le service recrée ce qu'il attend.

## 🔢 Exercice 5 : plein, avec des fichiers vides

Créez des fichiers vides dans un tmpfs de 4 Mio limité à 20 entrées :

```bash
docker run --rm --read-only --tmpfs /espace:size=4m,nr_inodes=20 "$IMAGE" sh -c '
for i in $(seq 30); do touch /espace/f$i 2>/dev/null; done
ls /espace | wc -l
touch /espace/encore
df -k /espace | tail -1
df -i /espace | tail -1'
```

```text
19
touch: /espace/encore: No space left on device
tmpfs                     4096         0      4096   0% /espace
tmpfs                       20        20         0 100% /espace
```

Le message dit que la place manque, et `df -k` montre qu'elle est entière : ce
sont les entrées qui manquent. Devant `No space left on device`, lisez les deux
`df`.

## 🤐 Exercice 6 : une écriture perdue en silence

Lancez un programme qui ignore ses erreurs, puis un autre qui choisit son
dossier temporaire :

```bash
docker run --rm --read-only "$IMAGE" sh -c '(echo ligne > /var/log/app.log) 2>/dev/null; echo "travail fini"'; echo "code: $?"
docker run --rm --read-only "$IMAGE" mktemp; echo "code: $?"
docker run --rm --read-only -e TMPDIR=/dev/shm "$IMAGE" sh -c 'mktemp > /dev/null'; echo "code: $?"
```

```text
travail fini
code: 0
mktemp: : Read-only file system
code: 1
code: 0
```

Le premier rend 0 et n'a rien écrit : un conteneur qui tourne ne prouve pas que
le service travaille. Contrôlez le résultat attendu. Beaucoup de programmes
suivent `TMPDIR`, ce qui évite d'ouvrir `/tmp`.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-fige > /dev/null
rm -rf ~/essai-fige
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
dsoxlab reset container-systeme-en-lecture-seule
dsoxlab check container-systeme-en-lecture-seule
```

```text
╭─ Résultat : container-systeme-en-lecture-seule ─╮
│  0 / 100 pts                                    │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests                │
╰─────────────────────────────────────────────────╯
```

0 sur 2 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un worker à figer, qui doit continuer à donner signe
de vie.

```bash
dsoxlab run container-systeme-en-lecture-seule
dsoxlab challenge container-systeme-en-lecture-seule
```
