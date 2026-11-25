# Bloquer une image sur un vrai scan hors ligne daté

La leçon lit un rapport et écrit une barrière sur une CVE. Ce cours s'attaque à
la preuve elle-même : un inventaire effacé, un nom qui a bougé, des versions
mal comparées, un refus perdu en route, et un rapport trop vieux.

Vous travaillez dans `~/essai-preuve`, avec un petit script qui lit
l'inventaire Alpine d'une image sans la lancer. Le challenge porte sur
`/opt/lab-image-scan` : n'y touchez pas pendant le cours.

Page associée : [Vérifier ce que contient une image, et qui l'a signée](https://www.stephane-robert.info/docs/conteneurisation/supply-chain-images/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run image-scan-de-vulnerabilites
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `inventaire.py` affiche
les paquets d'une image ; il rend 1 si le paquet interdit s'y trouve. **Gardez
le même terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-preuve && cd ~/essai-preuve
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cat > inventaire.py <<'EOF'
import io, json, subprocess, sys, tarfile, datetime
image, interdit, rapport = sys.argv[1:4]
lance = lambda *a: subprocess.run(["docker", *a], check=True, capture_output=True).stdout
c = lance("create", image).decode().strip()
try:
    t = tarfile.open(fileobj=io.BytesIO(lance("export", c)))
    try:
        texte = t.extractfile("lib/apk/db/installed").read().decode()
    except KeyError:
        texte = ""
finally:
    lance("rm", c)
noms = sorted(l[2:] for l in texte.splitlines() if l.startswith("P:"))
json.dump({"image": image, "id": lance("image", "inspect", "-f", "{{.Id}}", image).decode().strip(),
           "date": datetime.datetime.now().isoformat(), "paquets": noms}, open(rapport, "w"))
print(len(noms), "paquets,", "refuse" if interdit in noms else "accepte")
sys.exit(interdit in noms)
EOF
python3 inventaire.py "$IMAGE" zlib r.json; echo "code: $?"
```

```text
29.9.2
16 paquets, refuse
code: 1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🕳️ Exercice 1 : un inventaire effacé

Retirez l'inventaire d'une image, sans retirer la bibliothèque, et refaites le
contrôle :

```bash
printf 'ARG IMAGE\nFROM $IMAGE\nRUN rm /lib/apk/db/installed\n' > Dockerfile
docker build -q --build-arg IMAGE="$IMAGE" -t essai-sans . > /dev/null
python3 inventaire.py essai-sans zlib r.json; echo "code: $?"
docker run --rm essai-sans sh -c 'ls /usr/lib /lib | grep -c libz'
```

```text
0 paquets, accepte
code: 0
2
```

Zéro paquet, donc accepté, alors que la bibliothèque est toujours là. Un
contrôle qui n'a rien trouvé à lire doit refuser, pas accepter. Ce n'est pas un
cas d'école : les fichiers copiés sans paquet ne sont pas vus non plus.

## 🏷️ Exercice 2 : un nom qui a bougé

Contrôlez une étiquette, déplacez-la sur une autre image, et relisez le rapport
:

```bash
docker tag essai-sans essai-candidate
python3 inventaire.py essai-candidate zlib r.json
docker tag "$IMAGE" essai-candidate
python3 -c 'import json; print("rapport sur", json.load(open("r.json"))["image"])'
[ "$(python3 -c 'import json; print(json.load(open("r.json"))["id"])')" = "$(docker image inspect essai-candidate --format '{{.Id}}')" ] && echo 'meme image' || echo 'autre image'
```

```text
0 paquets, accepte
rapport sur essai-candidate
autre image
```

Le rapport cite la bonne étiquette, et il parle d'une autre image. Comparez
l'identifiant de l'image au moment de la décision, pas son nom.

## 🔢 Exercice 3 : des versions mal comparées

Comparez trois couples de versions, en texte puis avec l'outil de Debian :

```bash
compare() {
  [ "$(printf '%s\n%s\n' "$1" "$2" | LC_ALL=C sort | head -1)" = "$1" ] && T='plus ancienne' || T='plus recente'
  dpkg --compare-versions "$1" lt "$2" && O='plus ancienne' || O='plus recente'
  echo "$1 face a $2 : texte $T, dpkg $O"
}
compare 3.0.9-1 3.0.17-1
compare 1.1.1n-0+deb11u5 1.1.1w-0+deb11u1
compare 3.0.17-1~deb12u2 3.0.17-1
compare 1:1.0-1 2.0-1
```

```text
3.0.9-1 face a 3.0.17-1 : texte plus recente, dpkg plus ancienne
1.1.1n-0+deb11u5 face a 1.1.1w-0+deb11u1 : texte plus ancienne, dpkg plus ancienne
3.0.17-1~deb12u2 face a 3.0.17-1 : texte plus recente, dpkg plus ancienne
1:1.0-1 face a 2.0-1 : texte plus ancienne, dpkg plus recente
```

Le texte se trompe dès qu'un nombre prend un chiffre de plus, et sur le `~`,
qui place une version **avant** celle qu'il prolonge. L'époque, devant les
deux-points, passe avant tout. Une distribution corrige aussi sans changer de
version amont : ne comparez jamais avec le numéro de l'éditeur seul.

## 🕳️ Exercice 4 : un refus perdu en route

Enveloppez le contrôle de quatre façons, et lisez le code rendu :

```bash
printf '#!/bin/sh\npython3 inventaire.py "$1" zlib r.json | tee journal\n' > a.sh
printf '#!/bin/sh\npython3 inventaire.py "$1" zlib r.json\necho fini\n' > b.sh
printf '#!/bin/sh\nif ! python3 inventaire.py "$1" zlib r.json; then echo alerte; fi\n' > c.sh
printf '#!/bin/bash\nset -o pipefail\npython3 inventaire.py "$1" zlib r.json | tee journal\n' > d.sh
chmod +x ?.sh
for s in a b c d; do ./$s.sh "$IMAGE" > /dev/null; echo "$s.sh : $?"; done
```

```text
a.sh : 0
b.sh : 0
c.sh : 0
d.sh : 1
```

Trois enveloppes sur quatre rendent 0 alors que l'image est refusée : un tube,
une commande qui suit, un `if` sans sortie. Éprouvez une barrière avec une
image qui doit être refusée, pas seulement avec une bonne.

## ⏰ Exercice 5 : un rapport trop vieux

Vieillissez un rapport de trois jours, puis comparez la date du fichier et
celle du contenu :

```bash
python3 inventaire.py "$IMAGE" absent r.json
python3 -c 'import json, datetime as d; r = json.load(open("r.json")); r["date"] = (d.datetime.now() - d.timedelta(days=3)).isoformat(); json.dump(r, open("r.json", "w"))'
find r.json -mmin -60 | grep -q . && echo 'fichier : recent'
python3 -c 'import json, datetime as d; a = d.datetime.now() - d.datetime.fromisoformat(json.load(open("r.json"))["date"]); print("contenu :", a.days, "jours")'
touch -d '3 days ago' r.json; find r.json -mmin -60 | grep -q . || echo 'fichier : ancien'
```

```text
16 paquets, accepte
fichier : recent
contenu : 3 jours
fichier : ancien
```

La date du fichier change au moindre `touch` ou à la copie, dans un sens comme
dans l'autre. Celle du contenu se modifie aussi à la main. Seul un contrôle
refait au moment de décider répond à la question : que dit la base d'alertes
aujourd'hui ?

## 🧹 Nettoyage

```bash
cd ~
docker rmi -f essai-sans essai-candidate > /dev/null
rm -rf ~/essai-preuve
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
dsoxlab reset image-scan-de-vulnerabilites
dsoxlab check image-scan-de-vulnerabilites
```

```text
╭─ Résultat : image-scan-de-vulnerabilites ─╮
│  0 / 100 pts                              │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests          │
╰───────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : une preuve fidèle, une image à promouvoir, et une
barrière qui refuse vraiment.

```bash
dsoxlab run image-scan-de-vulnerabilites
dsoxlab challenge image-scan-de-vulnerabilites
```
