# Audit de l'ancien `containers-training`

État mesuré le 2026-10-01, avant reconstruction. Chaque constat porte la
commande qui l'établit : un audit dont les affirmations ne se rejouent pas ne
vaut rien, et c'est la règle de tous les catalogues de ce compte.

Le dépôt audité est `stephrobert/containers-training` à son commit `03e7aae`,
168 étoiles, 47 forks, licence CC BY-SA 4.0.

## Ce qu'il contenait

```console
$ find . -type f -not -path './.git/*' | wc -l
35
```

| Répertoire | Fichiers | Contenu réel |
| --- | --- | --- |
| `00-Docker/` | 17 | cinq TP en markdown, 1101 lignes, plus les sources d'une API FastAPI |
| `01-Docker-compose/` | 1 | un `.gitkeep` |
| `02-Docker-swarm/` | 1 | un `.gitkeep` |
| `03-Kubernetes/` | 16 | quatre sections de TP Kubernetes |

Le README annonçait les quatre répertoires sur le même plan. Deux d'entre eux
ne contenaient rien.

## Le défaut de fond : des TP qui donnent les commandes

Les cinq TP sont des **pas-à-pas**. Ils enseignent, et ils enseignent bien,
mais ils ne mesurent rien : l'apprenant qui recopie les blocs arrive au
résultat sans qu'aucun contrôle ne distingue le travail compris du travail
recopié.

C'est le partage que la refonte installe, et il n'est pas propre à ce dépôt :

```text
www.stephane-robert.info     explique, enseigne
containers-dsoxlab-training   fait pratiquer, mesure, prouve
```

Un TP qui réexplique le guide crée une seconde description du même sujet, qui
divergera. Les 42 guides du périmètre comptent 525 sections : la matière
pédagogique existe déjà, et elle est maintenue là.

## Quatre défauts pédagogiques, mesurés

### Alpine présentée comme exempte de vulnérabilités

```console
$ git show main:00-Docker/03-alpine/01-contruction-3eme-image.md | grep -n 'aucune vulnér'
🎯 L'image Alpine ne contient à ce jour aucune vulnérabilité !
```

Et dans le bilan du même TP : « Vérifier la sécurité de l'image avec Trivy ».

Deux erreurs en une. Un scan ne dit pas qu'une image est sûre : il dit ce que
sa base de vulnérabilités connaît, à cet instant, des paquets qu'il a su
identifier. Alpine affiche souvent moins de constats parce que ses paquets sont
moins nombreux et que sa base est différente, pas parce que son code est sain.
Le « à ce jour » atténue à peine, et la phrase est mémorisée sans lui.

Un lab de scan doit faire constater l'inverse : la même image, scannée deux
mois plus tard, rend d'autres résultats sans qu'une ligne ait bougé.

### L'utilisateur non-root annoncé « optionnel »

```console
$ git show main:00-Docker/04-multistage-build/01-contruction-image-finale.md | grep -B2 USER
# Utilisateur non-root (optionnel)
RUN adduser -D appuser
USER appuser
```

C'est le seul des cinq TP qui mentionne `USER` :

| TP | occurrences de `USER` |
| --- | --- |
| 01-debian12-basique | 0 |
| 02-debian12-optimisee | 0 |
| 03-alpine | 0 |
| 04-multistage-build | 1, annotée « optionnel » |
| 05-volumes | 0 |

Un conteneur qui tourne en root partage l'UID 0 avec l'hôte : une évasion donne
root sur la machine. Ce n'est pas une option de confort, et le présenter ainsi
installe l'habitude inverse de celle qu'on veut.

### Le volume NFS sur `127.0.0.1`

```console
$ git show main:00-Docker/05-volumes/01-volumes_docker.md | grep -A4 'type=nfs'
  --opt type=nfs \
  --opt o=addr=127.0.0.1,nolock,soft,rw \
  --opt device=:/chemin/du/partage/nfs \
```

Précédé de « Pour cet exercice, vous devez avoir un partage NFS actif sur
l'hôte », et l'étape est marquée « facultatif ».

Un exercice qui suppose un serveur NFS que rien n'installe n'est pas
facultatif : il est infaisable. Et `127.0.0.1` ne désigne pas la même chose
selon qui l'écrit — le démon Docker le résout depuis l'hôte, pas depuis le
conteneur.

### L'ordre des couches qui invalide le cache

```dockerfile
WORKDIR /app
COPY app/ /app/
RUN pip3 install --break-system-packages -r requirements.txt
```

Le `COPY` précède l'installation. Toute modification du code applicatif, qui
est ce qui change le plus souvent, invalide la couche des dépendances, qui est
ce qui change le moins. Un build qui prenait dix-sept secondes de cache les
perd entièrement pour une ligne de Python.

C'est l'un des deux ou trois réflexes qui comptent vraiment dans un Dockerfile,
et le TP l'enseigne à l'envers sans le dire.

## Deux défauts de forme

**Les dépendances ne sont pas épinglées.** `requirements.txt` portait `fastapi`
et `uvicorn[standard]`, sans version. La même image, reconstruite dans six
mois, n'embarque plus le même code : un TP qui compare des tailles ne compare
plus rien.

**Les emoji sont partout** dans ce que l'apprenant lit, y compris dans les
titres de section. La doctrine des catalogues les proscrit : ils survivent mal
aux terminaux, aux lecteurs d'écran et aux copier-coller.

## Décisions, élément par élément

| Élément | Décision | Pourquoi |
| --- | --- | --- |
| `03-Kubernetes/` | **SUPPRIMER** | vit dans `kubernetes-dsoxlab-training` ; deux formations concurrentes sur un même sujet divergent |
| `01-Docker-compose/`, `02-Docker-swarm/` | **SUPPRIMER** | coquilles vides annoncées comme du contenu ; reviennent comme vrais blocs aux vagues 3 et 6 |
| Les cinq TP, en tant que textes | **SUPPRIMER** | le blog enseigne ; un pas-à-pas recopié ici divergerait de lui |
| Leur **substance** | **RÉÉCRIRE** en labs | la progression Debian → optimisation → Alpine → multi-étapes est juste, et c'est elle qu'on garde |
| `app/main.py`, `requirements.txt` | **CONSERVER** et étendre | l'API FastAPI devient le **fil rouge** du catalogue ; les dépendances sont épinglées |
| Le Dockerfile du TP2 | **RÉÉCRIRE** | son ordre de couches est le contre-exemple ; il devient le point de départ fautif d'un lab sur le cache |
| L'étape NFS du TP5 | **SUPPRIMER** d'ici | un serveur NFS exige une vraie machine : le sujet appartient à un lab `runtime: vm`, pas au poste de l'apprenant |
| La conclusion sur Alpine | **RÉÉCRIRE** à l'inverse | un lab de scan doit faire constater qu'un résultat est daté |
| `README.md` | **RÉÉCRIRE** | annonçait quatre sections dont deux vides, et se présentait comme « pas un cours, plutôt un guide » |

## Ce que la reconstruction récupère vraiment

Peu de lignes, et c'est normal : ce qui avait de la valeur n'était pas le texte,
c'était la **progression**. Quatre images successives sur la même application,
chacune mesurée contre la précédente, est une bonne idée pédagogique. Elle
devient la colonne `c2` du nouveau catalogue, avec des tests à la place des
captures de sortie.

```text
récupéré   : l'application FastAPI, la progression en quatre images,
             l'idée de mesurer chaque étape
jeté       : 1101 lignes de pas-à-pas, trois affirmations fausses,
             deux répertoires vides, 16 fichiers Kubernetes
```

## Ce que l'audit a trouvé et que le brief ne soupçonnait pas

**La même image mesure 83 Mio par l'API Docker et 329 Mio par `docker images`.**

```console
$ docker image inspect --format '{{.Size}}' <image>   #  83.0 Mio
$ docker image ls      --format '{{.Size}}' <image>   # 329.0 Mio
$ docker info --format '{{.DriverStatus}}'
[[driver-type io.containerd.snapshotter.v1]]
```

Le moteur emploie le **containerd image store** : l'API rend la taille
compressée, celle du registre, et la commande la taille décompressée sur
disque. Le classic image store rendait la seconde des deux côtés.

Les anciens TP affichaient des tailles tirées de `docker images`. Un lab qui
écrirait un seuil en octets lu par l'API recalerait un apprenant dont le
terminal affiche un chiffre quatre fois plus grand. Les labs d'optimisation
comparent donc des **rapports** entre deux images mesurées de la même façon,
ce qui a l'avantage de rester vrai quand les deux grossissent.

**Les ancres du blog ne se devinent pas.** Un premier slugifieur, qui retirait
les accents et remplaçait l'apostrophe par un tiret, tombait juste 26 fois sur
68. La règle réelle, mesurée contre les pages publiées, garde les accents et
supprime la ponctuation sans séparateur :

```text
'Prérequis'                     -> #prérequis
"Initialisation d'un cluster"   -> #initialisation-dun-cluster
"Qu'est-ce que Docker Swarm ?"  -> #quest-ce-que-docker-swarm-
'Exemple : workers uniquement'  -> #exemple--workers-uniquement
```

Corrigée, elle tombe juste **114 fois sur 114**. C'est ce qui rend tenable un
`doc_url` ancré sur la section exacte qu'un lab éprouve, là où un guide de 1095
lignes doit servir vingt labs.

Rien ne vérifie aujourd'hui qu'une ancre existe : `validate-structure
--check-urls` contrôle le code HTTP de la page, pas le fragment. Un vérificateur
du catalogue doit le faire.
