# Récupérer de l'espace dans un sandbox ENOSPC borné

La leçon trouve le montage plein et libère la place sans recréer. Ce cours
montre cinq cas où l'on se trompe de cause : deux montages et un seul message,
un fichier effacé qui occupe encore, une écriture à moitié faite, un coupable
que `ls` désigne mal, et un espace en mémoire qui tue avant d'être plein.

Vous travaillez sur des conteneurs `essai-*`, avec des espaces en mémoire de
quelques mégaoctets. Le challenge porte sur le `worker` de son projet : n'y
touchez pas pendant le cours.

Page associée : [Faire tourner les journaux, et reprendre du disque](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/journaux-et-espace-disque/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run troubleshoot-disque-plein
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-plein && cd ~/essai-plein
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
docker run -d --init --name essai-place --tmpfs /travail:size=4m --shm-size 2m "$IMAGE" sleep 600 > /dev/null
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🗺️ Exercice 1 : deux montages, un seul message

Remplissez `/dev/shm`, et comparez l'état des montages :

```bash
docker exec essai-place dd if=/dev/zero of=/dev/shm/x bs=1M count=3 2>&1 | grep dd:
docker exec essai-place df -m /dev/shm /travail / | awk 'NR>1{print $6, $5}' | sed 's/^\/ .*/\/ (disque de l hote)/'
docker exec essai-place rm /dev/shm/x
```

```text
dd: error writing '/dev/shm/x': No space left on device
/dev/shm 100%
/travail 0%
/ (disque de l hote)
```

`No space left on device` ne dit pas quel espace. Ici, ni le disque de l'hôte
ni `/travail` ne sont en cause : c'est `/dev/shm`, dont la taille se fixe à
part. Lisez toujours `df` sur le chemin exact qui a échoué.

## 👻 Exercice 2 : un fichier effacé qui occupe encore

Effacez un fichier qu'un programme tient ouvert :

```bash
docker exec essai-place dd if=/dev/zero of=/travail/a bs=1M count=3 2> /dev/null
docker exec -d essai-place sh -c 'exec 3< /travail/a; echo $$ > /tmp/pid; exec sleep 500'
sleep 1
docker exec essai-place rm /travail/a
docker exec essai-place sh -c 'du -sm /travail | cut -f1; df -m /travail | awk "NR==2{print \$3}"'
docker exec essai-place sh -c 'ls -l /proc/*/fd 2> /dev/null' | grep -o '/travail/a (deleted)'
docker exec essai-place sh -c 'kill $(cat /tmp/pid); sleep 1; df -m /travail | awk "NR==2{print \$3}"'
```

```text
0
3
/travail/a (deleted)
0
```

`du` ne voit plus rien, `df` compte toujours 3 Mo : le fichier n'a plus de nom,
mais un programme le lit encore. L'écart entre les deux est le signal. La place
revient quand le programme ferme le fichier ou s'arrête.

## ✂️ Exercice 3 : une écriture à moitié faite

Écrivez plus que la place, puis copiez un petit fichier :

```bash
docker exec essai-place sh -c 'yes ligne | head -c 6000000 > /travail/journal; echo "code: $?"' 2> /dev/null
docker exec essai-place stat -c '%s %n' /travail/journal
docker exec essai-place cp /etc/alpine-release /travail/copie; echo "code: $?"
docker exec essai-place stat -c '%s %n' /travail/copie
docker exec essai-place sh -c ': > /travail/journal; df -m /travail | awk "NR==2{print \$3}"'
```

```text
code: 1
4194304 /travail/journal
cp: write error: No space left on device
code: 1
0 /travail/copie
0
```

Les deux écritures échouent, et les deux laissent un fichier : un journal
coupé, une copie vide. Un fichier qui existe n'est donc pas un fichier écrit.
La dernière commande vide le journal sans l'effacer, ce qui rend la place même
si un programme le tient ouvert.

## 🕵️ Exercice 4 : un coupable mal désigné

Cherchez ce qui occupe la place, avec `ls` puis avec `du` :

```bash
docker exec essai-place sh -c 'rm -f /travail/*; dd if=/dev/zero of=/travail/reel bs=1M count=2 2> /dev/null; truncate -s 100M /travail/creux'
docker exec essai-place ls -l /travail | awk 'NR>1{print $5, $9}'
docker exec essai-place sh -c 'du -k /travail/* | sort -n'
```

```text
104857600 creux
2097152 reel
0	/travail/creux
2048	/travail/reel
```

`ls` annonce 100 Mo pour un fichier qui n'en occupe aucun, dans un espace de 4
Mo. Triez par `du` : c'est le seul qui compte les blocs réellement pris.

## 💀 Exercice 5 : un espace en mémoire qui tue

Donnez 100 Mo d'espace à un conteneur limité à 20 Mo de mémoire, et écrivez-en
60 :

```bash
docker run -d --init --name essai-memoire --memory 20m --memory-swap 20m --tmpfs /travail:size=100m "$IMAGE" sleep 600 > /dev/null
docker exec essai-memoire dd if=/dev/zero of=/travail/x bs=1M count=60 > /dev/null 2>&1; echo "code: $?"
docker inspect essai-memoire --format '{{.State.Status}} OOMKilled={{.State.OOMKilled}}'
docker exec essai-memoire df /travail 2>&1 | grep -o 'possibly OOM-killed'
docker rm -f essai-memoire > /dev/null
```

```text
code: 137
running OOMKilled=true
possibly OOM-killed
```

Un tmpfs se paie en mémoire : l'écriture est tuée bien avant les 100 Mo, sans
message de disque plein. Le conteneur tourne encore, mais sa mémoire est
occupée par le fichier, et on ne peut plus y lancer une commande. Choisissez la
taille d'un tmpfs avec la limite de mémoire.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-place > /dev/null
rm -rf ~/essai-plein
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
dsoxlab reset troubleshoot-disque-plein
dsoxlab check troubleshoot-disque-plein
```

```text
╭─ Résultat : troubleshoot-disque-plein ─╮
│  0 / 100 pts                           │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests       │
╰────────────────────────────────────────╯
```

0 sur 2 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un espace plein, un reçu à garder, et un conteneur à
ne pas recréer.

```bash
dsoxlab run troubleshoot-disque-plein
dsoxlab challenge troubleshoot-disque-plein
```
