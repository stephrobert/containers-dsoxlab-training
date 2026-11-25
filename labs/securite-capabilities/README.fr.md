# Rendre à un service la seule capability dont il a besoin

La leçon retire toutes les capabilities et cherche l'exception à partir d'une
erreur. Ce cours montre ce qui fausse cette recherche : un compte non root, une
liste mal écrite, un root sans pouvoir, une porte d'administration, et un
masque mal lu.

Vous travaillez sur des conteneurs `essai-*`. Le challenge porte sur le
`worker` de son projet : n'y touchez pas pendant le cours.

Page associée : [Durcir le runtime : capabilities et privilèges](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/securite/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run securite-capabilities
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-pouvoirs && cd ~/essai-pouvoirs
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
J="docker run --rm --network none"
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 👤 Exercice 1 : un compte non root

Regardez les masques d'un conteneur lancé sous l'UID 1000, puis ajoutez-lui une
capability :

```bash
$J --user 1000 "$IMAGE" grep -E '^Cap(Eff|Bnd)' /proc/1/status
$J --user 1000 --cap-add NET_ADMIN "$IMAGE" grep -E '^Cap(Eff|Bnd)' /proc/1/status
```

```text
CapEff:	0000000000000000
CapBnd:	00000000a80425fb
CapEff:	0000000000000000
CapBnd:	00000000a80435fb
```

Le plafond `CapBnd` grandit, et `CapEff` reste à zéro : pour un compte non
root, `--cap-add` ne donne rien au processus. Il élève seulement ce qu'un
programme setuid pourrait atteindre. Lisez `CapEff` pour savoir ce que le
service peut faire.

## ✍️ Exercice 2 : une liste mal écrite

Essayez une faute de frappe, deux façons d'écrire le même nom, et des listes
contradictoires :

```bash
$J --cap-add CHWON "$IMAGE" true 2>&1 | grep -o 'unknown capability.*'
$J --cap-drop ALL --cap-add cap_chown "$IMAGE" grep CapEff /proc/1/status
$J --cap-drop ALL --cap-add chown "$IMAGE" grep CapEff /proc/1/status
$J --cap-drop CHOWN --cap-add CHOWN "$IMAGE" grep CapEff /proc/1/status
$J --cap-add ALL --cap-drop ALL "$IMAGE" grep CapEff /proc/1/status
```

```text
unknown capability: "CAP_CHWON"
CapEff:	0000000000000001
CapEff:	0000000000000001
CapEff:	00000000a80425fb
CapEff:	000001ffffffffff
```

Une faute arrête le lancement, et la casse comme le préfixe n'ont pas
d'importance. Les deux dernières lignes sont plus dangereuses : entre un ajout
et un retrait du même nom, l'ajout l'emporte. `ALL` des deux côtés donne tous
les pouvoirs du noyau.

## 🪫 Exercice 3 : un root sans pouvoir

Faites faire quatre gestes ordinaires à un root sans capability :

```bash
$J --cap-drop ALL "$IMAGE" sh -c 'echo s > /tmp/f; chmod 000 /tmp/f; cat /tmp/f; echo "lire: $?"'
$J --cap-drop ALL "$IMAGE" sh -c 'su nobody -s /bin/sh -c id; echo "changer de compte: $?"'
$J --cap-drop ALL "$IMAGE" sh -c 'sleep 60 & kill $!; echo "tuer son enfant: $?"'
$J --cap-drop ALL "$IMAGE" sh -c 'echo a > /tmp/f; chmod 600 /tmp/f; echo "chmod de son fichier: $?"'
```

```text
cat: can't open '/tmp/f': Permission denied
lire: 1
su: can't set groups: Operation not permitted
changer de compte: 1
tuer son enfant: 0
chmod de son fichier: 0
```

Root y redevient un compte soumis aux droits, jusque sur un fichier à lui. Ce
qui touche ses propres fichiers et processus marche encore. Le message change
aussi : `Permission denied` au lieu de `Operation not permitted`. Ne cherchez
donc pas une seule phrase dans les journaux.

## 🚪 Exercice 4 : une porte d'administration

Entrez dans un conteneur sans capability, normalement puis avec `--privileged`
:

```bash
docker run -d --init --name essai-nu --cap-drop ALL "$IMAGE" sleep 600 > /dev/null
docker exec essai-nu grep CapEff /proc/self/status
docker exec --privileged essai-nu grep CapEff /proc/self/status
docker exec --privileged essai-nu chown 5 /etc/motd; echo "code: $?"
docker exec essai-nu grep CapEff /proc/1/status
docker rm -f essai-nu > /dev/null
```

```text
CapEff:	0000000000000000
CapEff:	000001ffffffffff
code: 0
CapEff:	0000000000000000
```

`docker exec --privileged` donne tous les pouvoirs au processus ajouté, et pas
au service. Un essai fait de cette façon ne prouve rien sur le service. C'est
aussi une raison de plus de surveiller qui peut joindre le moteur.

## 🔢 Exercice 5 : un masque mal lu

Traduisez le masque par défaut, puis comparez le même processus vu du conteneur
et de l'hôte :

```bash
python3 -c 'm = 0xa80425fb; print(bin(m).count("1"), [i for i in range(41) if m >> i & 1])'
python3 -c 'print(hex(1 << 0), hex(1 << 10), hex(1 << 13))'
docker run -d --init --name essai-masque --cap-drop ALL --cap-add CHOWN "$IMAGE" sleep 600 > /dev/null
docker exec essai-masque grep CapEff /proc/1/status
grep CapEff "/proc/$(docker inspect essai-masque --format '{{.State.Pid}}')/status"
docker exec --user 1000 essai-masque grep CapEff /proc/self/status
docker rm -f essai-masque > /dev/null
```

```text
14 [0, 1, 3, 4, 5, 6, 7, 8, 10, 13, 18, 27, 29, 31]
0x1 0x400 0x2000
CapEff:	0000000000000001
CapEff:	0000000000000001
CapEff:	0000000000000000
```

Chaque capability est un bit : la 0 donne `0x1`, la 10 donne `0x400`. Le masque
se lit aussi bien de l'hôte. Le dernier vaut zéro, parce que `/proc/self`
désigne la commande lancée sous un autre compte : lisez toujours `/proc/1`.

## 🧹 Nettoyage

```bash
cd ~
rm -rf ~/essai-pouvoirs
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
dsoxlab reset securite-capabilities
dsoxlab check securite-capabilities
```

```text
╭─ Résultat : securite-capabilities ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests   │
╰────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un lanceur qui s'arrête sans ses pouvoirs, et un seul
à lui rendre.

```bash
dsoxlab run securite-capabilities
dsoxlab challenge securite-capabilities
```
