# Limiter un conteneur fait main

La leçon crée un cgroup, y pose trois plafonds (`memory.max`, `pids.max`,
`cpu.max`), puis retire des capabilities avec `setpriv`. Ce cours vous fait
voir ce qu'elle ne montre pas. D'abord, où systemd a déjà rangé vos propres
processus. Ensuite, comment déplacer un processus déjà lancé, et comment
freiner la mémoire sans tuer. Puis comment vider un groupe d'un seul geste.
Enfin, vous lirez un masque de capabilities sans outil de décodage, et vous
mesurerez pourquoi l'ordre `unshare` puis `setpriv` n'est pas un détail.

Vous travaillez avec des cgroups nommés `essai-*` et des processus de l'hôte,
sans conteneur. Le challenge porte sur un autre cgroup, d'autres plafonds et un
conteneur détaché : vous le ferez seul, à la fin.

Page associée : [Limiter un conteneur : cgroups v2 et capabilities](https://www.stephane-robert.info/docs/conteneurisation/limiter-un-conteneur/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run conteneur-limiter-a-la-main
```

Vous êtes maintenant connecté à `oci.lab`, une Debian 13 sans aucun moteur de
conteneurs. Vous êtes l'utilisateur `ansible`, et `sudo` vous donne les droits
de root. **Gardez le même terminal jusqu'au nettoyage** : les variables des
exercices n'existent que dans lui.

```bash
setpriv --version
uname -r
cat /sys/fs/cgroup/cgroup.subtree_control
```

```text
setpriv from util-linux 2.41.5
6.12.118+deb13-amd64
cpu memory pids
```

Les sorties de ce cours ont été relevées sur cette machine le 24 novembre 2026,
avec util-linux 2.41.5 et le noyau 6.12 de Debian 13.8. La dernière ligne
liste les contrôleurs que la racine transmet à ses enfants : `cpu`, `memory`
et `pids`, les trois dont vous aurez besoin.

## 🗂️ Exercice 1 : où vit votre shell

La leçon crée un cgroup à la racine de l'arbre. Mais tout processus est déjà
dans un cgroup, y compris votre shell. Regardez lequel, puis la branche que
systemd tient pour votre utilisateur :

```bash
cat /proc/self/cgroup
systemd-cgls --no-pager -u user.slice | head -8
```

```text
0::/user.slice/user-1001.slice/session-431.scope
Unit user.slice (/user.slice):
└─user-1001.slice
  ├─session-333.scope
  │ ├─35673 sshd-session: ansible [priv]
  │ └─35681 sshd-session: ansible@notty
  ├─session-431.scope
  │ ├─46049 sshd-session: ansible [priv]
  │ ├─46057 sshd-session: ansible@notty
```

Votre shell vit dans `session-<n>.scope`, sous `user-1001.slice` (1001 est
l'uid d'`ansible`), sous `user.slice`. C'est systemd qui a créé cette branche
à votre connexion SSH : il range chaque session, chaque service et chaque
utilisateur dans son propre cgroup. C'est pour cela que la leçon rappelle
qu'en production, on passe par systemd plutôt que d'écrire à la main sous
`/sys/fs/cgroup`.

## 🚚 Exercice 2 : déplacer un processus déjà lancé

Dans la leçon, le conteneur naît dans son cgroup. Un processus déjà lancé peut
aussi y entrer : il suffit d'écrire son numéro dans `cgroup.procs`. Créez un
cgroup d'essai, lancez un `sleep`, et déplacez-le :

```bash
CG=/sys/fs/cgroup/essai-tardif
sudo mkdir "$CG"
P=$(sleep 600 > /dev/null 2>&1 & echo $!)
cat /proc/$P/cgroup
echo "$P" | sudo tee "$CG/cgroup.procs" > /dev/null
cat /proc/$P/cgroup
cat "$CG/pids.current"
```

```text
0::/user.slice/user-1001.slice/session-431.scope
0::/essai-tardif
1
```

Le `sleep` est passé de votre session au cgroup `essai-tardif`, sans être
relancé, et `pids.current` le compte. Ce geste ne déplace que ce processus :
ses enfants déjà lancés restent où ils sont. Seuls ceux qu'il lancera ensuite
naîtront dans le nouveau groupe. D'où la méthode de la leçon : placer le
processus **avant** qu'il lance le conteneur.

## 🐢 Exercice 3 : freiner la mémoire sans tuer

`memory.max` est un mur : au-delà, le noyau tue. `memory.high` est un frein :
au-delà, le noyau récupère de la mémoire et ralentit le groupe, sans tuer
personne. Posez un frein à 32M, sans swap, et lancez le même `tail /dev/zero`
que la leçon, arrêté au bout de 5 secondes par `timeout` :

```bash
CF=/sys/fs/cgroup/essai-frein
sudo mkdir "$CF"
echo 32M | sudo tee "$CF/memory.high" > /dev/null
echo 0 | sudo tee "$CF/memory.swap.max" > /dev/null
sudo bash -c "echo \$\$ > $CF/cgroup.procs; exec timeout 5 tail /dev/zero"; echo "code retour: $?"
grep -E '^(high|max|oom|oom_kill) ' "$CF/memory.events"
cat "$CF/memory.peak"
```

```text
code retour: 124
high 398
max 0
oom 0
oom_kill 0
38604800
```

Le code 124 est celui de `timeout` : c'est lui qui a arrêté `tail`, pas le
noyau. Le compteur `high` a monté, `oom_kill` est resté à 0, et
`memory.peak` a un peu dépassé 32M (33 554 432 octets). Le frein est souple :
le groupe peut le franchir un instant, puis le noyau le ralentit. Un moteur
de conteneurs pose surtout `memory.max`. `memory.high` sert à prévenir avant
le mur.

## 🧨 Exercice 4 : vider un groupe d'un seul geste

La leçon arrête son conteneur par `pkill`, processus par nom. Le fichier
`cgroup.kill` tue **tout** le contenu d'un groupe, quel que soit le nom des
processus. Ajoutez trois `sleep` au groupe de l'exercice 2, puis videz-le :

```bash
for i in 1 2 3; do echo "$(sleep 601 > /dev/null 2>&1 & echo $!)" | sudo tee "$CG/cgroup.procs" > /dev/null; done
cat "$CG/pids.current"
echo 1 | sudo tee "$CG/cgroup.kill" > /dev/null
sleep 1
cat "$CG/pids.current"
```

```text
4
0
```

Quatre processus avant, zéro après : le noyau a envoyé `SIGKILL` à chacun.
Le groupe est maintenant vide, donc il peut être retiré. C'est le geste du
`cleanup.yaml` de ce lab, et celui qu'emploient les moteurs pour arrêter un
conteneur entier.

## 🔍 Exercice 5 : lire un masque de capabilities

La leçon cite `capsh --decode`. Sur cette machine, `capsh` est installé
(`/usr/sbin/capsh`, du paquet `libcap2-bin`), mais `/usr/sbin` n'est pas
dans le `PATH` de l'utilisateur `ansible` : il ne se lance que par `sudo`.
On peut s'en passer. `setpriv --list-caps` liste les capabilities dans
l'ordre des bits, en partant de 0. Regardez les lignes 19 à 23 de cette liste,
numérotées à partir de 0, puis les masques de votre shell, avec et sans
`sudo` :

```bash
setpriv --list-caps | nl -v0 | sed -n '19,23p'
setpriv --list-caps | wc -l
grep CapEff /proc/self/status
sudo grep CapEff /proc/self/status
```

```text
    18	sys_chroot
    19	sys_ptrace
    20	sys_pacct
    21	sys_admin
    22	sys_boot
41
CapEff:	0000000000000000
CapEff:	000001ffffffffff
```

`sys_admin` porte le numéro 21, sur les 41 capabilities de ce noyau. Votre
shell n'a aucune capability effective (`CapEff` à 0), et `sudo` les donne
toutes. Pour savoir si un masque contient `sys_admin`, il suffit de lire son
bit 21. Le shell sait le faire seul :

```bash
M=$(sudo setpriv --bounding-set=-sys_admin --inh-caps=-sys_admin grep CapBnd /proc/self/status | cut -f2)
echo "masque: $M"
echo "bit 21 (sys_admin): $(( (0x$M >> 21) & 1 ))"
M=$(sudo grep CapBnd /proc/self/status | cut -f2)
echo "masque: $M"
echo "bit 21 (sys_admin): $(( (0x$M >> 21) & 1 ))"
```

```text
masque: 000001ffffdfffff
bit 21 (sys_admin): 0
masque: 000001ffffffffff
bit 21 (sys_admin): 1
```

Le premier masque vient d'un processus lancé par `setpriv` : son bit 21 vaut
0. Le second est celui de `sudo` seul : son bit 21 vaut 1. C'est le contrôle
que vous pourrez faire sur le conteneur du challenge, depuis l'hôte.

## ⚖️ Exercice 6 : pourquoi l'ordre compte

La leçon dit que `setpriv` vient **après** `unshare`. Mesurez ce qui se passe
dans l'autre ordre, puis dans le bon :

```bash
sudo setpriv --bounding-set=-sys_admin --inh-caps=-sys_admin unshare --uts hostname essai-ordre; echo "code retour: $?"
sudo unshare --uts setpriv --bounding-set=-sys_admin --inh-caps=-sys_admin hostname essai-ordre; echo "code retour: $?"
hostname
```

```text
unshare: unshare failed: Operation not permitted
code retour: 1
hostname: you must be root to change the host name
code retour: 1
oci.lab
```

Dans le mauvais ordre, `unshare` échoue : créer un namespace exige
`CAP_SYS_ADMIN`, qui vient d'être retirée. Dans le bon ordre, le namespace
`uts` est créé, puis `hostname` est refusé. Notez le message : « you must be
root ». Le processus est pourtant root (uid 0). Ce qui lui manque, c'est la
capability. Un message d'erreur qui parle de root désigne souvent une
capability absente.

## 🧹 Nettoyage

Retirez les deux cgroups d'essai, qui sont vides, puis vérifiez qu'il ne reste
rien :

```bash
sudo rmdir /sys/fs/cgroup/essai-tardif /sys/fs/cgroup/essai-frein
ls -d /sys/fs/cgroup/essai-* 2>/dev/null || echo "aucun cgroup d'essai"
pgrep -a -f 'sleep 60[01]' || echo "aucun processus d'essai"
```

```text
aucun cgroup d'essai
aucun processus d'essai
```

Plus rien de ce cours. Quittez ensuite la machine et remettez le lab à zéro.
`dsoxlab reset` rejoue le nettoyage puis la préparation du lab : vous
retrouvez exactement l'état de départ du challenge. Il vous demande de
confirmer : répondez `y`.

```bash
exit
dsoxlab reset conteneur-limiter-a-la-main
dsoxlab check conteneur-limiter-a-la-main
```

```text
╭─ Résultat : conteneur-limiter-a-la-main ─╮
│  0 / 100 pts                             │
│  ░░░░░░░░░░░░░░░░░░░░  0/5 tests         │
╰──────────────────────────────────────────╯
```

0 sur 5 : c'est le résultat attendu. Le challenge vous attend, intact.

## 🎯 Le challenge

À vous, seul cette fois : enfermer un conteneur détaché dans un cgroup qui
plafonne sa mémoire, ses processus et son CPU, retirer `CAP_SYS_ADMIN` à son
root, et voir le noyau tuer un processus qui dépasse le plafond.

```bash
dsoxlab run conteneur-limiter-a-la-main
dsoxlab challenge conteneur-limiter-a-la-main
```
