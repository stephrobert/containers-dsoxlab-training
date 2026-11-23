# Migrer une image vers un socle léger

La leçon montre ce que fournit un socle, pourquoi changer la ligne `FROM` fait
échouer un script ou un binaire, et comment choisir entre réécrire et
réinstaller. Ce cours vous fait relever le contrat d'un troisième socle,
diagnostiquer un shebang qui passe par `env`, débusquer une construction bash
qui échoue sans bruit, réparer les fuseaux horaires d'Alpine, et prouver par
les couches qu'une image a bien changé de socle.

Vous travaillez dans `~/essai-socle`, avec des images `essai-socle:*`. Le
challenge porte sur une autre application et un autre script : vous le ferez
seul, à la fin.

Page associée : [Choisir une image de base](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/choisir-une-image-de-base/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-migrer-vers-alpine
```

Vous êtes maintenant connecté à `docker.lab`, une Debian 13 où le moteur
Docker tourne. Créez le répertoire d'essai, et rangez dans deux variables les
socles de ce cours, épinglés par leur digest. **Gardez le même terminal
jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-socle && cd ~/essai-socle
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
BUSYBOX=busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

Les sorties de ce cours ont été relevées sur cette machine le 23 novembre 2026,
avec Docker Engine 29.9.2.

## 🔎 Exercice 1 : relever le contrat d'un troisième socle

La leçon compare Alpine et Debian. Relevez le même contrat sur `busybox`, un
socle encore plus petit : sa libc, son gestionnaire de paquets, ses
certificats racine et son nombre de comptes.

```bash
for image in "$ALPINE" "$BUSYBOX"; do
  echo "== ${image%%@*}"
  docker run --rm "$image" sh -c 'ls /lib/libc.musl-x86_64.so.1 >/dev/null 2>&1 && echo musl || { ls /lib/libc.so.6 >/dev/null 2>&1 && echo glibc || echo "libc ?"; }; command -v apk || echo "pas de apk"; ls /etc/ssl/certs/ca-certificates.crt 2>/dev/null || echo "certificats absents"; wc -l < /etc/passwd'
done
```

```text
== alpine:3.24.3
musl
/sbin/apk
/etc/ssl/certs/ca-certificates.crt
17
== busybox:1.37.0
Unable to find image 'busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec' locally
docker.io/library/busybox@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec: Pulling from library/busybox
68fe9bff2ad4: Pulling fs layer
68fe9bff2ad4: Download complete
68fe9bff2ad4: Pull complete
9177639ff916: Download complete
Digest: sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
Status: Downloaded newer image for busybox@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
glibc
pas de apk
certificats absents
9
```

L'image `busybox` par défaut est construite sur la **glibc**, pas sur musl
comme Alpine. Elle n'a ni gestionnaire de paquets ni certificats racine, et
seulement 9 comptes. On ne peut rien y installer : tout ce qu'une application
y réclame doit être copié à la construction. Les lignes `Pulling` du début
viennent du premier téléchargement de l'image.

## 🐍 Exercice 2 : un shebang qui passe par env

Beaucoup de scripts commencent par `#!/usr/bin/env python3`, pour trouver
l'interpréteur où qu'il soit. Livrez un tel script sur Alpine, puis
lancez-le :

```bash
printf '#!/usr/bin/env python3\nprint("bonjour")\n' > salut && chmod +x salut
printf 'FROM %s\nCOPY salut /usr/local/bin/salut\nCMD ["/usr/local/bin/salut"]\n' "$ALPINE" > Dockerfile.env
docker build -q -t essai-socle:env -f Dockerfile.env .
docker run --rm essai-socle:env; echo "code=$?"
docker run --rm --entrypoint sh essai-socle:env -c 'head -1 /usr/local/bin/salut; command -v python3 || echo "python3 absent"'
```

```text
sha256:8bba4c2f7a7bed635dfd803dac53ccfc6fbd90533d7655a3385d0f5efb7890b4
env: can't execute 'python3': No such file or directory
code=127
#!/usr/bin/env python3
python3 absent
```

Le message n'est plus celui de la leçon. `env` existe sur Alpine : c'est lui
qui démarre, puis qui échoue en nommant enfin le vrai manquant, `python3`.
Avec un shebang direct (`#!/usr/bin/python3`), vous auriez eu le message
trompeur `no such file or directory` sur le script. Dans les deux cas, `head -1`
donne la réponse.

## 🔁 Exercice 3 : une construction bash qui échoue sans bruit

Un script annoncé `#!/bin/sh` peut contenir des constructions de bash. Écrivez
un script qui compte de 1 à 3 avec `{1..3}` et qui teste une variable avec
`[[ ]]`, puis lancez-le sur Alpine :

```bash
cat > compter <<'EOF'
#!/bin/sh
for i in {1..3}; do echo "tour $i"; done
if [[ -n "$HOME" ]]; then echo "maison=$HOME"; fi
EOF
chmod +x compter
printf 'FROM %s\nCOPY compter /usr/local/bin/compter\nCMD ["/usr/local/bin/compter"]\n' "$ALPINE" > Dockerfile.sh
docker build -q -t essai-socle:sh -f Dockerfile.sh .
docker run --rm essai-socle:sh; echo "code=$?"
```

```text
sha256:62493ff03d00529c3f1580f995260239894dc4c5805f758055e3c1c6109fac41
tour {1..3}
maison=/root
code=0
```

Aucune erreur, et le code de sortie vaut 0. Pourtant la boucle n'a fait qu'un
tour, avec `{1..3}` pris pour du texte : le shell d'Alpine ne connaît pas cette
expansion de bash et ne s'en plaint pas. `[[ ]]`, lui, a fonctionné, parce que
le shell de BusyBox l'accepte. Une migration se vérifie donc sur le
**résultat**, pas sur l'absence d'erreur. Réécrivez le script en POSIX, puis
relancez :

```bash
cat > compter <<'EOF'
#!/bin/sh
for i in 1 2 3; do echo "tour $i"; done
if [ -n "$HOME" ]; then echo "maison=$HOME"; fi
EOF
docker build -q -t essai-socle:sh -f Dockerfile.sh .
docker run --rm essai-socle:sh; echo "code=$?"
```

```text
sha256:1fa164957d4f8c927512b043363bd5a9b666c457cd2656b02087f5ba57b12da4
tour 1
tour 2
tour 3
maison=/root
code=0
```

Trois tours cette fois. La liste `1 2 3` et le test `[ ]` sont compris de tous
les shells POSIX, et le script ne dépend plus de celui du socle.

## 🕒 Exercice 4 : des fuseaux horaires absents

La leçon note qu'Alpine n'a pas de base des fuseaux horaires. Demandez l'heure
de Paris à un conteneur Alpine, puis ajoutez le paquet `tzdata` et
recommencez. `docker history` mesure ce que le paquet ajoute :

```bash
docker run --rm -e TZ=Europe/Paris "$ALPINE" date +'%H:%M %Z'
printf 'FROM %s\nRUN apk add --no-cache tzdata\n' "$ALPINE" > Dockerfile.tz
docker build -q -t essai-socle:tz -f Dockerfile.tz .
docker run --rm -e TZ=Europe/Paris essai-socle:tz date +'%H:%M %Z'
docker history --format '{{.Size}}\t{{.CreatedBy}}' essai-socle:tz | head -2 | cut -c1-70
```

```text
18:27 UTC
sha256:a06000a39ad5d907377f512dca48b7d1188b71dcef3711ac471ba756a51931b5
19:27 CET
1.66MB	RUN /bin/sh -c apk add --no-cache tzdata # b…
0B	CMD ["/bin/sh"]
```

Sans `tzdata`, la variable `TZ` est ignorée sans message : l'heure reste en
UTC. Avec le paquet, elle passe à l'heure de Paris (CET, une heure de plus en
novembre). La couche ajoutée pèse environ 1,7 Mo : c'est le prix de cette
réparation, à comparer aux 9 Mo du socle.

## 🧱 Exercice 5 : prouver par les couches qu'une image a changé de socle

L'image `essai-socle:tz` est construite sur Alpine. Comparez ses couches à
celles du socle :

```bash
docker image inspect "$ALPINE" --format '{{range .RootFS.Layers}}{{println .}}{{end}}' | grep -v '^$'
echo --
docker image inspect essai-socle:tz --format '{{range .RootFS.Layers}}{{println .}}{{end}}' | grep -v '^$'
```

```text
sha256:75c137aedfb2760f88629236cb7b797630aed0c3d91d626d1d1bb694878fc2ba
--
sha256:75c137aedfb2760f88629236cb7b797630aed0c3d91d626d1d1bb694878fc2ba
sha256:3c631e868767dbe538bea1f033b4ed196580b98d76d986dc1499a34d598f1322
```

Le socle n'a qu'une couche, et elle est la **première** de l'image : c'est la
preuve que l'image repose sur lui. La seconde couche est celle du `RUN apk add`.
Une image construite sur un autre socle aurait une autre première couche, même
si elle pesait le même poids.

## 🧹 Nettoyage

Supprimez les images d'essai, l'image `busybox` téléchargée et le répertoire.
La dernière commande compte ce qui reste :

```bash
cd ~
docker rmi essai-socle:env essai-socle:sh essai-socle:tz | grep -c Untagged
docker rmi "$BUSYBOX" >/dev/null; rm -rf ~/essai-socle
docker images --format '{{.Repository}}' | grep -c -e '^essai-' -e '^busybox$'
```

```text
3
0
```

Plus rien de ce cours. Quittez ensuite la machine et remettez le lab à zéro.
`dsoxlab reset` rejoue le nettoyage puis la préparation du lab : vous
retrouvez exactement l'état de départ du challenge. Il vous demande de
confirmer : répondez `y`.

```bash
exit
dsoxlab reset images-migrer-vers-alpine
dsoxlab check images-migrer-vers-alpine
```

```text
╭─ Résultat : images-migrer-vers-alpine ─╮
│  0 / 100 pts                           │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests       │
╰────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge vous attend, intact.

## 🎯 Le challenge

À vous, seul cette fois : faire passer une application d'un socle Debian à un
socle Alpine, sans perdre son résultat, et prouver qu'elle a vraiment changé
de socle.

```bash
dsoxlab run images-migrer-vers-alpine
dsoxlab challenge images-migrer-vers-alpine
```
