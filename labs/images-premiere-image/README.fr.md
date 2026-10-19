# Ce qu'une image contient, et ce qu'elle oublie

Une image n'est pas une archive de votre projet. C'est un système de fichiers
complet, empilé en couches, plus quelques métadonnées qui disent comment le
démarrer. Ce lab fait construire la première, et il insiste sur ce qu'on
découvre d'habitude en production : ce qu'on a oublié dedans.

Toutes les sorties de cette page ont été capturées sur une exécution réelle.
Les exemples sont volontairement étrangers au challenge : ils démontrent, ils
ne se copient pas.

## Une image de base est un système, pas un langage

Le réflexe est de prendre une image « qui a Python ». Voyons d'abord ce que
donne une image de système nu :

```console
$ docker run --rm debian:12 python3 --version
docker: Error response from daemon: failed to create task for container: failed
to create shim task: OCI runtime create failed: runc create failed: unable to
start container process: error during container init: exec: "python3":
executable file not found in $PATH
```

Le message est long, et la seule partie qui compte est la fin :
`executable file not found in $PATH`. Debian 12 est une distribution, pas un
environnement d'exécution. Elle porte un gestionnaire de paquets, un shell, des
bibliothèques système, et c'est tout.

On peut l'installer à la main dans un conteneur :

```console
$ docker run --rm debian:12 bash -c 'apt-get -qq update && apt-get -qq install -y cowsay && ls /usr/games'
cowsay
cowthink
```

Deux constats. L'installation fonctionne, donc l'image de base sait installer
des paquets. Et le conteneur a disparu avec `--rm`, `cowsay` avec lui : **ce
qu'on installe dans un conteneur en cours d'exécution ne survit pas**. C'est
pour cela qu'un Dockerfile existe.

## Chaque instruction qui touche aux fichiers ajoute une couche

Prenons un Dockerfile jetable, qui affiche un horodatage :

```dockerfile
FROM debian:12
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/demo
COPY horodatage.txt /opt/demo/
CMD ["cat", "/opt/demo/horodatage.txt"]
```

Combien de couches ? La question mérite d'être posée plutôt que devinée :

```console
$ docker image inspect debian:12 --format '{{len .RootFS.Layers}}'
1
$ docker image inspect demo --format '{{len .RootFS.Layers}}'
4
```

Une pour l'image de base, et trois ajoutées. L'historique dit lesquelles, et
avec quel poids :

```console
$ docker image history demo --format '{{.Size}}  {{.CreatedBy}}'
0B        CMD ["cat" "/opt/demo/horodatage.txt"]
16.4kB    COPY horodatage.txt /opt/demo/ # buildkit
12.3kB    WORKDIR /opt/demo
12.2MB    RUN /bin/sh -c apt-get update && apt-get ins…
133MB     # debian.sh --arch 'amd64' out/ 'bookworm' …
```

**`WORKDIR` crée une couche**, et c'est contre-intuitif : il crée le
répertoire, donc il modifie le système de fichiers. `CMD` pèse `0 B` : il ne
touche à rien, il renseigne la configuration de l'image.

Le poids est l'autre leçon de cette sortie. L'image de base fait 133 Mo, le
`RUN` en ajoute 12,2, et les deux dernières instructions quelques kilooctets.
C'est presque toujours ainsi : ce qui coûte, c'est le socle et les paquets, pas
votre code.

Le `rm -rf /var/lib/apt/lists/*` sur la même ligne que l'installation n'est pas
une coquetterie. Sur une ligne séparée, il effacerait ces fichiers dans une
nouvelle couche, et la précédente les contiendrait toujours : l'image porterait
les deux. Les labs d'optimisation de cette série mesurent exactement cela.

## `EXPOSE` ne publie rien

C'est la confusion la plus fréquente. `EXPOSE` **documente** le port que
l'image sert ; c'est `-p`, au lancement, qui le publie :

```console
$ docker run -d --name demo-expose -p 127.0.0.1:9999:80 nginx:alpine
$ docker inspect demo-expose --format '{{.Config.ExposedPorts}}'
map[80/tcp:{}]
```

Une image sans `EXPOSE` se publie très bien ; une image avec `EXPOSE` et sans
`-p` n'est joignable de nulle part. Ce que `EXPOSE` apporte, c'est que le
lecteur, Compose et les outils savent quel port demander sans lire votre code.

## Une application qui n'écoute que sur elle-même

Dans un conteneur, la boucle locale est celle du conteneur. Un serveur lancé
sur `127.0.0.1` est joignable depuis l'intérieur, et par personne d'autre :

```console
$ docker run -d --name demo-boucle -p 127.0.0.1:9998:8000 python:3.12-slim \
    python -m http.server 8000 --bind 127.0.0.1

$ curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9998/
000

$ docker exec demo-boucle python -c \
    "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/').status)"
200
```

Le conteneur se répond à lui-même, l'hôte n'obtient rien, et `-p` était bien
là. La correction est dans l'application, pas dans le lancement : elle doit
écouter sur `0.0.0.0`, c'est-à-dire sur toutes ses interfaces.

## Debian 12 protège son Python

Une dernière surprise, propre aux distributions récentes :

```console
$ docker run --rm debian:12 bash -c 'apt-get -qq update && apt-get -qq install -y python3-pip && pip3 install rich'
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.

    If you wish to install a non-Debian-packaged Python package,
    [...]
```

C'est la PEP 668. Le gestionnaire de paquets de la distribution et `pip` se
disputeraient les mêmes fichiers, donc Debian ferme la porte. Deux réponses
existent : un environnement virtuel, ou dire à `pip` qu'on assume. Dans un
conteneur dédié à **une seule** application, il n'y a pas d'autre environnement
à protéger, et la seconde est légitime. La leçon jumelée détaille les deux, et
un lab plus loin dans la série emploie la première.

## Ce que la vérification regarde

Les sept contrôles lisent l'image que vous aurez construite et ce que
l'application répond. Le dernier la lance **sans aucun réseau** et exige
qu'elle réponde quand même.

C'est la seule façon de distinguer une image qui embarque son application d'une
image qui télécharge au démarrage, et les deux se ressemblent tant qu'Internet
répond. C'est précisément la panne que le scénario raconte.

## À vous

```bash
dsoxlab run   images-premiere-image
dsoxlab check images-premiere-image
dsoxlab hint  images-premiere-image
```

Référence : [écrire un Dockerfile](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/)
