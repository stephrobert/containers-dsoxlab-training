# Trois accès refusés, trois causes

La leçon sépare trois causes : le montage, les droits et le mode du fichier. Ce
cours vous fait rencontrer cinq refus qui leur ressemblent, et que ces trois
vérifications n'expliquent pas.

Vous travaillez dans `~/essai-refus`, sur des conteneurs `essai-*`. Le
challenge porte sur `perm-a`, `perm-b`, `perm-c` et `temoin-sans-bit` : n'y
touchez pas pendant le cours.

Page associée : [Droits sur un volume Docker : trois causes courantes d'un accès refusé](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/droits-sur-un-volume/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run troubleshoot-permission-refusee
```

Vous êtes connecté à `docker.lab`, où le moteur tourne, et l'image d'Alpine est
sur la machine. **Gardez le même terminal jusqu'au nettoyage** : les variables
n'existent que dans lui.

```bash
mkdir -p ~/essai-refus && cd ~/essai-refus
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🚪 Exercice 1 : un répertoire parent fermé

Le fichier est lisible par tous, et il est refusé :

```bash
mkdir -p coffre/dossier && echo bonjour > coffre/dossier/note && chmod 644 coffre/dossier/note && chmod 700 coffre
docker run --rm --user 4343 -v "$PWD/coffre:/coffre" "$IMAGE" cat /coffre/dossier/note
docker run --rm -v "$PWD/coffre:/coffre" "$IMAGE" stat -c '%a %n' /coffre /coffre/dossier /coffre/dossier/note
```

```text
cat: can't open '/coffre/dossier/note': Permission denied
700 /coffre
775 /coffre/dossier
644 /coffre/dossier/note
```

Il faut pouvoir traverser chaque répertoire du chemin. Le premier, en 700,
arrête tout le monde sauf son propriétaire. Lisez les droits de chaque étage,
pas seulement ceux du fichier.

## 🧱 Exercice 2 : une racine en lecture seule

Le message est celui d'un montage en lecture seule, et le conteneur n'a aucun
montage :

```bash
docker run -d --name essai-racine --read-only "$IMAGE" sleep 600 > /dev/null
docker exec essai-racine touch /marque
docker container inspect essai-racine --format '{{len .Mounts}} montage(s), ReadonlyRootfs={{.HostConfig.ReadonlyRootfs}}'
```

```text
touch: /marque: Read-only file system
0 montage(s), ReadonlyRootfs=true
```

`.Mounts` est vide : la question du mode de montage n'a pas de réponse ici.
C'est la racine elle-même qui refuse, par l'option `--read-only`, visible dans
`.HostConfig.ReadonlyRootfs`.

## ⛔ Exercice 3 : un montage qui interdit d'exécuter

Le script est exécutable, et l'exécution est refusée :

```bash
docker run -d --name essai-noexec --tmpfs /outils:noexec "$IMAGE" sleep 600 > /dev/null
docker exec essai-noexec sh -c 'printf "#!/bin/sh\necho lance\n" > /outils/o.sh; chmod 755 /outils/o.sh; stat -c %a /outils/o.sh; /outils/o.sh'
docker exec essai-noexec sh -c 'grep " /outils " /proc/mounts | grep -o noexec'
docker exec essai-noexec sh /outils/o.sh
```

```text
755
sh: /outils/o.sh: Permission denied
noexec
lance
```

Le mode est bon, c'est le montage qui porte `noexec`. `/proc/mounts`, lu dans
le conteneur, donne les options réelles. La dernière commande réussit, parce
que c'est `sh` qui s'exécute et lit le script.

## 👑 Exercice 4 : root, et pourtant refusé

Root lit d'ordinaire tous les fichiers. Retirez-lui la capability qui le permet
:

```bash
docker run --rm -v "$PWD/coffre:/coffre" "$IMAGE" cat /coffre/dossier/note
docker run --rm --cap-drop DAC_OVERRIDE --cap-drop DAC_READ_SEARCH -v "$PWD/coffre:/coffre" "$IMAGE" sh -c 'id -u; cat /coffre/dossier/note'
```

```text
bonjour
0
cat: can't open '/coffre/dossier/note': Permission denied
```

L'uid est 0 et l'accès est refusé : `DAC_OVERRIDE` est le pouvoir de root
d'ignorer les droits des fichiers. Un conteneur durci par `--cap-drop` se
comporte donc comme un utilisateur ordinaire face aux fichiers des autres.

## 🧊 Exercice 5 : un fichier immuable

Posez l'attribut d'immuabilité sur un fichier de l'hôte, puis essayez de le
modifier en root dans un conteneur :

```bash
echo fige > fige.txt
sudo chattr +i fige.txt
docker run --rm -v "$PWD:/d" "$IMAGE" sh -c 'stat -c %a /d/fige.txt; echo x >> /d/fige.txt'
lsattr fige.txt | cut -c1-6
sudo chattr -i fige.txt
docker run --rm -v "$PWD:/d" "$IMAGE" sh -c 'echo x >> /d/fige.txt && tail -1 /d/fige.txt'
```

```text
664
sh: can't create /d/fige.txt: Operation not permitted
----i-
x
```

`Operation not permitted`, et non `Permission denied` : le noyau ne discute pas
des droits, il interdit l'opération. Ni `stat` ni l'inspection du conteneur ne
le montrent. `lsattr`, sur l'hôte, affiche le `i`.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-racine essai-noexec > /dev/null
rm -r ~/essai-refus
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
dsoxlab reset troubleshoot-permission-refusee
dsoxlab check troubleshoot-permission-refusee
```

```text
╭─ Résultat : troubleshoot-permission-refusee ─╮
│  0 / 100 pts                                 │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests             │
╰──────────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : trois refus, trois causes à séparer, et aucune
réparation en root.

```bash
dsoxlab run troubleshoot-permission-refusee
dsoxlab challenge troubleshoot-permission-refusee
```
