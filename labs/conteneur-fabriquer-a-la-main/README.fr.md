# Fabriquer un conteneur à la main

La leçon fabrique un conteneur d'une seule commande `unshare`, puis l'observe
avec `lsns`, `nsenter` et `/proc`. Ce cours reprend les briques une par une.
Vous allez voir ce que change chaque namespace pris seul, et tomber dans le
piège d'un namespace `pid` sans son `/proc`. Vous vérifierez aussi plusieurs
copies d'un fichier avec un fichier de sommes. Vous verrez que l'hôte utilise
déjà des namespaces. Enfin, vous lancerez un conteneur détaché qui vous rend la
main, et vous lirez les numéros d'un périphérique avant d'en créer un.

Vous travaillez dans `~/essai-isolation`, avec des processus nommés `essai-*`
et sans changer de racine. Le challenge porte sur un autre système de fichiers
et un autre nom de machine : vous le ferez seul, à la fin.

Page associée : [Un conteneur à la main avec unshare et nsenter](https://www.stephane-robert.info/docs/conteneurisation/conteneur-a-la-main/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run conteneur-fabriquer-a-la-main
```

Vous êtes maintenant connecté à `oci.lab`, une Debian 13 sans aucun moteur de
conteneurs. Vous êtes l'utilisateur `ansible`, et `sudo` vous donne les droits
de root. Créez le répertoire d'essai. **Gardez le même terminal jusqu'au
nettoyage** : une variable de l'exercice 5 n'existe que dans lui.

```bash
mkdir -p ~/essai-isolation && cd ~/essai-isolation
unshare --version
uname -r
```

```text
unshare from util-linux 2.41.5
6.12.118+deb13-amd64
```

Les sorties de ce cours ont été relevées sur cette machine le 23 novembre 2026,
avec util-linux 2.41.5 et le noyau 6.12 de Debian 13.8.

## 🧱 Exercice 1 : un namespace à la fois

La leçon crée cinq namespaces d'un coup. Créez-en un seul, et regardez ce qu'il
isole et ce qu'il laisse partagé. D'abord `uts`, qui porte le nom de machine :

```bash
sudo unshare --uts sh -c 'hostname essai-uts; echo "nom: $(hostname)"; echo "processus visibles: $(ps -e --no-headers | wc -l)"'
echo "hôte: $(hostname)"
```

```text
nom: essai-uts
processus visibles: 120
hôte: oci.lab
```

Le shell porte un autre nom, et l'hôte garde le sien. Mais il voit toujours
plus d'une centaine de processus : ceux de l'hôte. Un namespace `uts` n'isole
que le nom. Faites la même chose avec `net`, qui porte les interfaces réseau,
et comparez avec l'hôte :

```bash
sudo unshare --net ip -brief link
ip -brief link
```

```text
lo               DOWN           00:00:00:00:00:00 <LOOPBACK>
lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
enp1s0           UP             52:54:d1:29:00:12 <BROADCAST,MULTICAST,UP,LOWER_UP>
```

Dans son namespace `net`, le processus ne voit qu'une interface `lo`, éteinte
(`DOWN`). L'hôte, lui, a `lo` allumée et sa carte `enp1s0`. Chaque namespace
isole une seule ressource du noyau. Un conteneur, c'est leur somme.

## 🪤 Exercice 2 : `--pid` sans `--mount-proc`

La leçon dit que `--mount-proc` est nécessaire, sans montrer ce qui se passe
quand on l'oublie. Créez un namespace `pid` sans cette option :

```bash
sudo unshare --pid --fork sh -c 'echo "mon PID: $$"; echo "processus visibles: $(ps -e --no-headers | wc -l)"; ps -o pid,comm -p 1'
```

```text
mon PID: 1
processus visibles: 121
    PID COMMAND
      1 systemd
```

Le shell se sait PID 1 : `$$` vient du noyau. Mais `ps` voit toujours tous les
processus de l'hôte, et nomme `systemd` comme PID 1. La raison : `ps` ne
demande rien au noyau, il lit le répertoire `/proc`. Ce `/proc` est celui de
l'hôte, monté pour l'ancien namespace. Ajoutez l'option et comparez :

```bash
sudo unshare --pid --fork --mount-proc sh -c 'echo "mon PID: $$"; ps -e -o pid,comm'
```

```text
mon PID: 1
    PID COMMAND
      1 sh
      2 ps
```

Cette fois, `ps` ne voit que le shell et lui-même. `--mount-proc` monte un
`/proc` neuf, qui décrit le nouveau namespace. Il implique `--mount`, pour que
ce montage ne touche pas le `/proc` de l'hôte. Retenez le symptôme : un PID 1
qui voit `systemd`, c'est un `/proc` qui n'a pas suivi.

## 🔏 Exercice 3 : vérifier des copies avec un fichier de sommes

La leçon vérifie une archive avec une somme passée en ligne de commande. Un
éditeur publie plutôt un fichier `SHA256SUMS`, qui liste les sommes de ses
fichiers. Créez un fichier, enregistrez sa somme, puis faites-en deux copies,
dont une modifiée d'un seul octet :

```bash
mkdir -p ~/essai-isolation/sommes && cd ~/essai-isolation/sommes
echo "version 1" > essai-a.txt
sha256sum essai-a.txt > SHA256SUMS
cat SHA256SUMS
mkdir -p copie-1 copie-2
cp essai-a.txt copie-1/
printf 'version 1 ' > copie-2/essai-a.txt
```

```text
3a79bf37b571938d1f2907afb6a643f48088b83769dde8bc58f5ee866a5c3636  essai-a.txt
```

`sha256sum -c` relit le fichier de sommes, cherche chaque fichier nommé dans le
répertoire courant, et compare. Lancez-le depuis chaque copie, en désignant le
fichier de sommes du répertoire parent :

```bash
cd ~/essai-isolation/sommes/copie-1 && sha256sum -c ../SHA256SUMS 2>&1; echo "code retour: $?"
cd ~/essai-isolation/sommes/copie-2 && sha256sum -c ../SHA256SUMS 2>&1; echo "code retour: $?"
cd ~/essai-isolation
```

```text
essai-a.txt: OK
code retour: 0
essai-a.txt: FAILED
sha256sum: WARNING: 1 computed checksum did NOT match
code retour: 1
```

La première copie répond `OK` et un code retour 0. La seconde répond `FAILED`
et un code 1 : l'espace ajoutée à la place du retour à la ligne suffit à
changer la somme. Les deux copies portent le même nom et pèsent les mêmes 10
octets : seule la somme fait la différence.

## 🔭 Exercice 4 : l'hôte utilise déjà des namespaces

Les namespaces ne sont pas réservés aux conteneurs. Listez les namespaces `uts`
de la machine, alors qu'aucun conteneur n'y tourne :

```bash
sudo lsns -t uts
systemctl show systemd-logind -p ProtectHostname
```

```text
        NS TYPE NPROCS   PID USER             COMMAND
4026531838 uts     113     1 root             /sbin/init
4026532274 uts       1   399 root             ├─/usr/lib/systemd/systemd-udevd
4026532277 uts       1   392 systemd-timesync ├─/usr/lib/systemd/systemd-timesyncd
4026532286 uts       1   779 root             ├─/usr/lib/systemd/systemd-logind
4026532345 uts       1   817 polkitd          └─/usr/lib/polkit-1/polkitd --no-debug --log-level=notice
ProtectHostname=yes
```

La première ligne est le namespace de l'hôte, partagé par plus d'une centaine
de processus. Les autres appartiennent à des services de systemd, comme
`systemd-logind` ou `systemd-timesyncd`. Leur unité porte
`ProtectHostname=yes`, qui leur interdit de changer le nom de machine. systemd
applique cette règle en leur donnant un namespace `uts` à eux : un nom changé
là ne sortirait pas du namespace. Un namespace isole une ressource. Il ne fait
pas pour autant un conteneur : ces services gardent la racine de l'hôte et
voient tous ses processus.

## 🚀 Exercice 5 : un conteneur détaché

Dans la leçon, le conteneur garde le terminal pendant qu'il tourne. Lancez-en
un qui vous rend la main. `setsid -f` démarre le programme dans une session
neuve, sans terminal, et revient tout de suite. Les redirections le
détachent aussi de vos entrées et sorties :

```bash
sudo setsid -f unshare --pid --fork --mount-proc --uts sh -c 'hostname essai-detache; exec sleep 3601' < /dev/null > /dev/null 2>&1
sleep 1
PID=$(pgrep -n -f 'sleep 3601')
ps -o pid,ppid,sid,tty,comm -p "$PID"
```

```text
    PID    PPID     SID TT       COMMAND
  12448   12447   12447 ?        sleep
```

Le terminal vous est rendu. La colonne `TT` vaut `?` : le processus n'est
rattaché à aucun terminal. Son `SID` est celui de son parent `unshare` : il vit
dans sa propre session. Ce `PID` est son numéro vu de l'hôte. Le fichier
`status` du processus donne aussi son numéro vu de l'intérieur :

```bash
grep NSpid /proc/$PID/status
sudo nsenter --target "$PID" --uts hostname
hostname
```

```text
NSpid:	12448	1
essai-detache
oci.lab
```

La ligne `NSpid` porte un numéro par namespace `pid`, du plus haut au plus
bas : le numéro vu de l'hôte, puis 1, son numéro dans son conteneur.
`nsenter --uts` lit le nom de machine du conteneur sans toucher à celui de
l'hôte.

Le `exec sleep 3601` n'est pas là pour décorer. Le conteneur vit tant que son
PID 1 vit. Lancez un conteneur dont le programme se termine aussitôt :

```bash
sudo setsid -f unshare --pid --fork --mount-proc --uts sh -c 'hostname essai-court' < /dev/null > /dev/null 2>&1
sleep 1
pgrep -a -f essai-court || echo "plus aucun processus essai-court"
```

```text
plus aucun processus essai-court
```

Le shell a changé le nom de machine, puis il s'est terminé. Le noyau a alors
détruit son namespace `pid` : il ne reste rien à observer.

## 🔌 Exercice 6 : lire les numéros d'un périphérique

La leçon crée `/dev/null` avec les numéros `1` et `3`. Ces numéros ne
s'inventent pas : ils se lisent sur l'hôte. `ls -l` les affiche à la place de
la taille, et `stat` les donne en hexadécimal :

```bash
ls -l /dev/null /dev/zero /dev/urandom
stat -c '%n %F majeur=%t mineur=%T' /dev/null /dev/zero
```

```text
crw-rw-rw- 1 root root 1, 3 Nov 23 20:20 /dev/null
crw-rw-rw- 1 root root 1, 9 Nov 23 20:20 /dev/urandom
crw-rw-rw- 1 root root 1, 5 Nov 23 20:20 /dev/zero
/dev/null character special file majeur=1 mineur=3
/dev/zero character special file majeur=1 mineur=5
```

Le `c` en tête de ligne indique un périphérique caractère. Le premier numéro
(majeur) désigne le pilote du noyau, le second (mineur) le périphérique de ce
pilote. Créez maintenant un vrai `null` et un faux, puis écrivez dans les
deux :

```bash
mkdir -p ~/essai-isolation/dev
sudo mknod -m 666 ~/essai-isolation/dev/null c 1 3
touch ~/essai-isolation/dev/faux-null
echo test > ~/essai-isolation/dev/null
echo test > ~/essai-isolation/dev/faux-null
ls -l ~/essai-isolation/dev
```

```text
total 4
-rw-rw-r-- 1 ansible ansible    5 Nov 23 20:37 faux-null
crw-rw-rw- 1 root    root    1, 3 Nov 23 20:37 null
```

Le vrai `null` affiche toujours `1, 3` et n'a rien gardé. Le faux est un
fichier ordinaire, qui a gardé les 5 octets écrits. Dans un conteneur, c'est
ce faux `null` qui grossit sans fin quand un programme y écrit en continu.

## 🧹 Nettoyage

Arrêtez le conteneur de l'exercice 5, retirez le répertoire d'essai, puis
vérifiez qu'il ne reste rien :

```bash
cd ~
sudo kill -KILL "$PID"
sleep 1
sudo rm -rf ~/essai-isolation
pgrep -a -f 'sleep 3601' || echo "aucun processus d'essai"
ls -d ~/essai-* 2>/dev/null || echo "aucun répertoire d'essai"
```

```text
aucun processus d'essai
aucun répertoire d'essai
```

Plus rien de ce cours. Quittez ensuite la machine et remettez le lab à zéro.
`dsoxlab reset` rejoue le nettoyage puis la préparation du lab : vous
retrouvez exactement l'état de départ du challenge. Il vous demande de
confirmer : répondez `y`.

```bash
exit
dsoxlab reset conteneur-fabriquer-a-la-main
dsoxlab check conteneur-fabriquer-a-la-main
```

```text
╭─ Résultat : conteneur-fabriquer-a-la-main ─╮
│  0 / 100 pts                               │
│  ░░░░░░░░░░░░░░░░░░░░  0/5 tests           │
╰────────────────────────────────────────────╯
```

0 sur 5 : c'est le résultat attendu. Le challenge vous attend, intact.

## 🎯 Le challenge

À vous, seul cette fois : fabriquer un conteneur sans moteur, à partir de la
bonne copie d'une archive, avec son nom de machine, ses namespaces et un vrai
`/dev/null`, et qui tourne encore après votre départ.

```bash
dsoxlab run conteneur-fabriquer-a-la-main
dsoxlab challenge conteneur-fabriquer-a-la-main
```
