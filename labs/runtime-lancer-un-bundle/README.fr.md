# Lancer un bundle OCI avec runc

La leçon fabrique un bundle avec `runc spec`, lit son `config.json` champ par
champ, suit le cycle de vie `create`, `start`, `kill`, `delete`, puis rejoue
le même bundle avec crun et en produit un avec umoci. Ce cours part du bundle
qu'écrit umoci et vous fait voir ce que la leçon ne montre pas. D'abord, que
sa racine est modifiable. Ensuite, pourquoi `runc kill` sans signal ne tue
rien, et ce que fait une pause. Puis ce que la liste des namespaces change
vraiment, comment écrire hors d'une racine en lecture seule, et pourquoi un
utilisateur non root garde ici des capabilities.

Vous travaillez sur Alpine 3.23, dans des dossiers nommés `/srv/essai-*`, avec
un conteneur nommé `essai`. Le challenge porte sur une autre image, un autre
bundle et un autre conteneur : vous le ferez seul, à la fin.

Page associée : [Exécuter un bundle OCI avec runc](https://www.stephane-robert.info/docs/conteneurisation/runtime-oci/).

## Avant de commencer

Lancez le lab :

```bash
dsoxlab run runtime-lancer-un-bundle
```

Vous êtes maintenant connecté à `oci.lab`, une Debian 13 sans aucun moteur de
conteneurs. Le bundle qu'écrit umoci appartient à root, en mode `0700` : passez
root pour tout le cours, comme dans la leçon.

```bash
sudo -i
runc --version
```

```text
runc version 1.1.15+ds1
commit: 1.1.15+ds1-2+deb13u1
spec: 1.2.0
go: go1.24.4
libseccomp: 2.6.0
```

Les sorties de ce cours ont été relevées sur cette machine le 26 novembre
2026, avec runc 1.1.15, la version du paquet Debian, et umoci 0.4.7. **Gardez
le même terminal jusqu'au nettoyage** : les variables des exercices n'existent
que dans lui.

Copiez Alpine 3.23 par son digest, transformez-la en bundle, puis lancez un
conteneur `essai` détaché, avec une commande qui dure :

```bash
A=docker://docker.io/library/alpine
A_INDEX=sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2
B=/srv/essai-bundle
skopeo copy -q --override-arch amd64 "$A@$A_INDEX" oci:/srv/essai-oci:3.23
umoci unpack --image /srv/essai-oci:3.23 "$B"
ls -ld "$B"
cat "$B/rootfs/etc/alpine-release"
cd "$B"
jq '.process.terminal=false | .process.args=["sleep","infinity"] | .hostname="essai"' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc list
```

```text
drwx------ 3 root root 4096 Nov 26 06:28 /srv/essai-bundle
3.23.8
ID          PID         STATUS      BUNDLE              CREATED                          OWNER
essai       112361      running     /srv/essai-bundle   2026-11-26T06:28:02.919315282Z   root
veilleur    0           stopped     /srv/ancien         2026-11-26T06:27:58.908270806Z   root
```

`runc run -d` lance le conteneur détaché et vous rend la main : il exige
`process.terminal` à `false`. `runc list` montre aussi `veilleur`, arrêté.
C'est le point de départ du challenge : n'y touchez pas pendant le cours.

## Exercice 1 : la racine qu'écrit umoci est modifiable

La leçon note que `runc spec` met la racine en lecture seule. Regardez ce
qu'écrit umoci, puis essayez d'écrire à la racine du conteneur :

```bash
jq -c '{root, namespaces: [.linux.namespaces[].type]}' config.json
runc exec essai touch /racine; echo "code $?"
ls -l rootfs/racine
```

```text
{"root":{"path":"rootfs"},"namespaces":["pid","network","ipc","uts","mount"]}
code 0
-rw-r--r-- 1 root root 0 Nov 26 06:28 rootfs/racine
```

Pas de `readonly` : la racine est modifiable, et le fichier écrit dans le
conteneur apparaît sur l'hôte, dans `rootfs`. Notez aussi les namespaces :
cinq, sans `cgroup`, là où `runc spec` en déclare six. Deux outils, deux
`config.json` par défaut différents. Lisez toujours celui que vous lancez.

Un conteneur qui tourne garde sa configuration. Pour passer en lecture seule,
supprimez-le, modifiez le fichier, puis relancez :

```bash
runc delete -f essai
rm rootfs/racine
jq '.root.readonly=true' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc exec essai touch /racine; echo "code $?"
```

```text
touch: /racine: Read-only file system
code 1
```

## Exercice 2 : le PID 1 ignore TERM

La leçon arrête le conteneur avec `runc kill demo KILL`. Essayez d'abord le
signal par défaut d'un arrêt propre, `TERM` :

```bash
runc kill essai TERM; sleep 2; runc state essai | jq -r .status
runc exec essai grep -E '^Sig(Cgt|Ign)' /proc/1/status
```

```text
running
SigIgn:	0000000000000000
SigCgt:	0000000000000000
```

Le conteneur tourne toujours. Dans son namespace `pid`, `sleep` est le PID 1,
et le noyau protège le PID 1 : un signal qu'il n'intercepte pas lui-même est
ignoré. `SigCgt` (les signaux interceptés) vaut zéro : `sleep` n'en intercepte
aucun. Seul `KILL`, que personne ne peut intercepter, l'arrête :

```bash
runc kill essai KILL; sleep 1; runc state essai | jq -r .status
runc delete essai
```

```text
stopped
```

C'est pour cela qu'un moteur attend quelques secondes après `TERM`, puis
envoie `KILL`. Une application qui tourne en PID 1 doit gérer `TERM`
elle-même pour s'arrêter proprement.

## Exercice 3 : une pause gèle le cgroup

runc sait aussi suspendre un conteneur sans l'arrêter. Relancez-le, trouvez
son cgroup, puis mettez-le en pause :

```bash
runc run -d essai
P=$(runc state essai | jq -r .pid)
cat /proc/$P/cgroup
CG=/sys/fs/cgroup$(cut -d: -f3 /proc/$P/cgroup)
runc pause essai; runc state essai | jq -r .status
cat "$CG/cgroup.freeze"
runc exec essai true; echo "code $?"
```

```text
0::/user.slice/user-1001.slice/essai
paused
1
time="2026-11-26T06:28:06Z" level=error msg="exec failed: cannot exec in a paused container (use --ignore-paused to override)"
code 255
```

Sans `cgroupsPath` dans le `config.json`, runc range le conteneur sous le
cgroup de celui qui le lance : ici votre session, `user-1001.slice`. La pause
écrit `1` dans `cgroup.freeze` : le noyau ne donne plus de temps processeur à
aucun processus du groupe. Un `runc exec` est refusé, puisque le nouveau
processus serait gelé lui aussi. La reprise remet `0` :

```bash
runc resume essai; cat "$CG/cgroup.freeze"
```

```text
0
```

## Exercice 4 : un namespace en moins, et le conteneur voit le réseau de l'hôte

runc ne fait rien pour le réseau : il crée un namespace `network` vide.
Regardez les interfaces du conteneur, puis retirez ce namespace de la liste et
relancez :

```bash
runc exec essai ip -o link | cut -d: -f2
runc delete -f essai
jq 'del(.linux.namespaces[] | select(.type=="network"))' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc exec essai ip -o link | cut -d: -f2
```

```text
 lo
 lo
 enp1s0
```

Avec le namespace, le conteneur n'a que `lo`, et personne ne lui branche de
câble : c'est le travail d'un moteur. Sans lui, il voit `enp1s0`, la carte
réseau de l'hôte. Chaque ligne de `linux.namespaces` est une isolation : la
retirer, c'est partager cette ressource avec l'hôte. Remettez-la avant de
continuer :

```bash
runc delete -f essai
jq '.linux.namespaces += [{"type":"network"}]' config.json > c.tmp && mv c.tmp config.json
```

## Exercice 5 : écrire hors d'une racine en lecture seule

La racine est en lecture seule, mais une application a souvent besoin d'écrire
quelque part. Montez un dossier de l'hôte dans le conteneur, en ajoutant une
entrée à `mounts` :

```bash
mkdir -p /srv/essai-donnees
jq '.mounts += [{"destination":"/donnees","type":"bind","source":"/srv/essai-donnees","options":["rbind","rw"]}]' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc exec essai sh -c 'date +%F > /donnees/trace && echo écrit'
cat /srv/essai-donnees/trace
runc delete -f essai
```

```text
écrit
2026-11-26
```

Le conteneur écrit dans `/donnees`, et le fichier se lit sur l'hôte dans
`/srv/essai-donnees`. La racine reste en lecture seule : seul ce dossier est
ouvert. C'est le principe des volumes d'un moteur.

## Exercice 6 : un utilisateur non root, et des capabilities quand même

Faites tourner le conteneur sous l'uid 1000, puis lisez ses masques de
capabilities :

```bash
jq '.process.user={"uid":1000,"gid":1000}' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc exec essai sh -c 'id; grep -E "^Cap(Eff|Bnd)" /proc/1/status'
jq -c '.process.capabilities.ambient' config.json
runc delete -f essai
```

```text
uid=1000 gid=1000
CapEff:	0000000020000420
CapBnd:	0000000020000420
["CAP_AUDIT_WRITE","CAP_KILL","CAP_NET_BIND_SERVICE"]
```

Le processus n'est plus root, mais ses capabilities effectives valent encore
`0000000020000420`, les trois de la leçon. La raison est dans le fichier :
umoci les place aussi dans la liste `ambient`, qu'un processus non root garde.
`id` n'affiche pas de nom : l'uid 1000 n'existe pas dans le `/etc/passwd`
d'Alpine. Videz les capabilities, et relancez :

```bash
jq '.process.capabilities={}' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc exec essai grep -E '^Cap(Eff|Bnd)' /proc/1/status
runc delete -f essai
```

```text
CapEff:	0000000000000000
CapBnd:	0000000000000000
```

Changer d'utilisateur ne suffit pas à retirer les droits : il faut aussi
regarder les capabilities que le fichier accorde.

## Nettoyage

Retirez tout ce que ce cours a créé, vérifiez qu'il ne reste rien, puis
quittez le shell root :

```bash
cd /
rm -rf /srv/essai-oci /srv/essai-bundle /srv/essai-donnees
ls -d /srv/essai-* 2>/dev/null || echo "aucun fichier d'essai"
runc list
exit
```

```text
aucun fichier d'essai
ID          PID         STATUS      BUNDLE        CREATED                          OWNER
veilleur    0           stopped     /srv/ancien   2026-11-26T06:27:58.908270806Z   root
```

Il ne reste que `veilleur`, posé par le lab. Quittez ensuite la machine et
remettez le lab à zéro. `dsoxlab reset` rejoue le nettoyage puis la
préparation du lab : vous retrouvez exactement l'état de départ du challenge.
Il vous demande de confirmer : répondez `y`.

```bash
exit
dsoxlab reset runtime-lancer-un-bundle
dsoxlab check runtime-lancer-un-bundle
```

```text
╭─ Résultat : runtime-lancer-un-bundle ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests      │
╰───────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge vous attend, intact.

## Le challenge

À vous, seul cette fois : libérer l'identifiant `veilleur`, transformer
busybox en bundle, régler sa commande, son nom de machine et sa racine en
lecture seule, et le garder en marche détaché.

```bash
dsoxlab run runtime-lancer-un-bundle
dsoxlab challenge runtime-lancer-un-bundle
```
