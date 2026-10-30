# Labs Conteneurs

**Langue :** [English](./README.md) · [Français](./README.fr.md)

[![CI](https://github.com/stephrobert/containers-dsoxlab-training/actions/workflows/ci.yml/badge.svg)](https://github.com/stephrobert/containers-dsoxlab-training/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/containers-dsoxlab-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/containers-dsoxlab-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/containers-dsoxlab-training.svg)](https://score.getplumber.io/github.com/stephrobert/containers-dsoxlab-training)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![Licence : CC BY 4.0](https://img.shields.io/badge/Licence-CC%20BY%204.0-lightgrey.svg)](./LICENSE)

Catalogue de **labs vérifiables** de la formation Conteneurisation du blog
[www.stephane-robert.info](https://www.stephane-robert.info/docs/conteneurs/),
joué par la CLI [dsoxlab](https://github.com/stephrobert/dsoxlab).

## Ce que c'est

Un ensemble d'exercices qui **mesurent** ce que vous savez faire. Chaque lab
pose un état de départ, vous donne une situation, et vérifie le résultat en
interrogeant le moteur Docker : l'image construite, sa taille, l'utilisateur
qui l'exécute, les montages du conteneur, ce que l'application répond.

Une même API FastAPI traverse tout le parcours et devient progressivement plus
correcte. **Vous n'avez pas besoin de savoir programmer** : le code est fourni.
Vous travaillez l'image, l'exécution, le réseau, le stockage, la distribution
et le durcissement.

## Ce que ce n'est pas

**Ce n'est pas un cours.** Les cours vivent sur le blog, et ce dépôt ne les
réécrit pas :

```text
www.stephane-robert.info     explique, enseigne
ce dépôt                      fait pratiquer, mesure, prouve
```

Chaque lab porte un `doc_url` vers la leçon qu'il éprouve, ancré sur la section
exacte. Si un lab vous résiste, la leçon est à un clic.

**Ce n'est pas une formation Kubernetes.** Kubernetes a son propre catalogue,
[kubernetes-dsoxlab-training](https://github.com/stephrobert/kubernetes-dsoxlab-training),
avec ses labs CKA, CKAD et CKS sur un cluster kubeadm réel. Rien ici ne parle
de `kubectl`, de Helm ou de manifests.

**Ce n'est pas une formation DevSecOps complète.** Trivy, Cosign, GitHub
Actions et GitLab CI apparaissent quand une compétence conteneur l'exige, et
pas davantage : ils ont leurs propres guides.

## Prérequis

| Ce qu'il faut | Pourquoi |
| --- | --- |
| **Un moteur Docker qui répond** | tous les labs l'interrogent. `docker info` doit aboutir |
| **`uv`** | il installe dsoxlab et l'outillage du catalogue |
| **`mise`**, facultatif | il pose hadolint, dive et trivy aux versions épinglées |

Docker n'est pas installé par ce catalogue : c'est un démon, avec un service,
un groupe d'utilisateurs et un socket. Le blog a un guide pour cela, et le
premier lab du parcours fait de sa vérification son sujet.

## Installation

```bash
# 1. dsoxlab, l'outil qui joue les labs
uv tool install dsoxlab

# 2. ce catalogue
git clone https://github.com/stephrobert/containers-dsoxlab-training.git
cd containers-dsoxlab-training

# 3. l'outillage épinglé, facultatif mais recommandé
mise install
```

Chaque lab se joue dans une **machine virtuelle jetable**, que
`dsoxlab provision` monte pour vous et que `dsoxlab destroy` retire. Vous
n'installez donc rien sur votre poste, Docker compris : c'est le lab qui pose
le moteur, dans une Debian 13 qui ne survit pas à la séance. Comptez quelques
minutes de provisionnement avant le premier lab.

### Votre premier lab, en cinq minutes

```bash
export LAB_HOME=$PWD

dsoxlab list-labs                        # ce que le catalogue contient
dsoxlab run       images-premiere-image  # pose le point de départ
dsoxlab challenge images-premiere-image  # la mission
# ... vous travaillez dans challenge/work ...
dsoxlab check     images-premiere-image  # le score
```

### Garder à jour

```bash
uv tool upgrade dsoxlab        # le moteur, publié sur PyPI
git -C <ce dépôt> pull         # le catalogue
```

Le moteur et le catalogue avancent indépendamment : un nouveau `dsoxlab` ne
demande jamais de recloner les labs, et de nouveaux labs ne demandent jamais de
mettre l'outil à jour, tant que la version du contrat correspond.

## Comment ça marche

### Le contrat déclaratif, à deux niveaux

Le catalogue est décrit par des données, pas par du code, et c'est ce qui garde
le moteur `dsoxlab` indépendant du domaine :

- **`meta.yml`** à la racine déclare l'identité du dépôt et l'**ordre** des
  huit sections affichées par `list-labs`, qui portent les identifiants des
  modules de la formation, plus le parcours Swarm déclaré hors tronc ;
- **`lab.yaml`** par lab déclare ses `skills`, son `level`, son `runtime`
  (type, fixtures, services), ses `distros`, son `doc_url` et un bloc
  `validation`. Un `lab.fr.yaml` surcharge `title` et `description` en
  français, et rien d'autre.

`dsoxlab validate-structure` contrôle tout le contrat, et les sections
déclarées dans `meta.yml` sans lab sont précisément la façon dont ce catalogue
dit ce qu'il doit encore.

### Le cycle de vie d'un lab

| Commande | Ce qu'elle fait |
| --- | --- |
| `dsoxlab list-labs` | le catalogue, dans l'ordre pédagogique |
| `dsoxlab run <id>` | copie le point de départ dans `challenge/work` |
| `dsoxlab challenge <id>` | la mission : ce qu'il faut obtenir, pas comment |
| `dsoxlab check <id>` | joue les tests et rend un score sur 100 |
| `dsoxlab hint <id>` | un indice, à un coût qui se déduit du score |
| `dsoxlab submit <id>` | enregistre le résultat définitivement |
| `dsoxlab progress` | où vous en êtes, lab par lab |
| `dsoxlab clean <id>` | retire le répertoire de travail |

### Les runtimes

| Runtime | Ce que le lab demande |
|---|---|
| `vm` | une Debian 13 jetable, montée par `dsoxlab provision` et détruite par `dsoxlab destroy`. Le lab y installe Docker ; les tests inspectent les images, conteneurs et réseaux que ce moteur contient vraiment. |

**Vous n'installez pas Docker sur votre poste.** C'est une décision de ce
catalogue, prise le 2026-10-28 : une machine virtuelle se jette, un démon
Docker posé sur votre machine de travail reste, avec son groupe `docker`, son
service et ses images. Les labs vous coûtent donc un `dsoxlab provision` de
quelques minutes, et rien d'autre.

En retour, ils peuvent enseigner ce qu'un conteneur sur votre poste
n'enseignerait pas : la configuration du démon, le mode rootless, seccomp,
AppArmor, le pare-feu, une registry avec son certificat. Et un lab qui remplit
le disque à dessein le remplit chez lui.

### Le modèle de validation

**Les tests lisent l'état, jamais vos commandes.**

Vous arrivez au résultat par le chemin que vous voulez. Un test de ce catalogue
ressemble à ceci :

```python
assert inspecter_image(tag)["Config"]["ExposedPorts"]   # ce que l'image déclare
code, corps = conteneur.repondre("/health")             # ce que l'application rend
assert conteneur.utilisateur() != "0"                   # qui l'exécute vraiment
```

Et jamais à ceci :

```python
assert "docker build" in historique   # ce qui ne prouve rien
```

### Score, indices, avancement

**Les indices ont un coût, et c'est voulu.**

Quatre indices par lab, du plus vague au plus explicite. Chacun retire des
points. Le dernier nomme l'outil qui montre la faute quand tout semble juste
sans l'être, mais aucun ne donne le Dockerfile.

### Trois niveaux d'exercice

| Type | Ce que vous recevez |
| --- | --- |
| `lab` | une explication et une mission ciblée |
| `challenge` | un objectif et des contraintes, pas de recette |
| `capstone` | une situation réelle, et le sujet du problème n'est pas annoncé |

Vous perdez progressivement les indications. C'est l'objet du parcours.

## Docker, Compose, Swarm : trois blocs distincts

| Bloc | Ce qu'il apprend | Ce qu'il exige |
| --- | --- | --- |
| **Docker** | images, exécution, données, réseau, sécurité, internes | une VM jetable |
| **Compose** | une application à plusieurs services, décrite et diagnostiquée | la même VM |
| **Swarm** | un orchestrateur distribué : Raft, quorum, overlay, secrets | plusieurs VM |

Swarm est un **parcours avancé, clairement séparé**. Ce n'est pas une étape
vers Kubernetes dans ce dépôt : c'est un orchestrateur à part entière, avec son
consensus et son état de contrôle à protéger.

## Le catalogue

<!-- LABS:START -->
### Utiliser les conteneurs

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `docker-verifier-son-moteur` | Le moteur fonctionne-t-il vraiment ? Quatre réponses, pas une | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/installation/#vérification-de-linstallation) |
| `docker-premier-conteneur` | Lancer, arrêter, supprimer : trois verbes qui ne se recouvrent pas | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/cli/#lancer-et-gérer-les-conteneurs-docker) |
| `docker-cycle-de-vie` | Le cycle de vie : redémarrer n'est pas recréer | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/concepts/#cycle-de-vie-dun-conteneur) |
| `container-entrypoint-et-cmd` | ENTRYPOINT et CMD : lequel vos arguments remplacent-ils ? | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#le-cycle-de-vie-dun-conteneur) |
| `container-signaux-et-pid-1` | Qui est PID 1 décide si votre conteneur s'arrête ou se fait tuer | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#stop-vs-kill--quelle-différence-) |
| `docker-inspecter-un-conteneur` | Interroger un conteneur en marche | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#les-commandes-indispensables) |
| `docker-anatomie-dune-image` | L'anatomie d'une image : couches, partage, configuration | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/#comment-est-construite-une-image-de-conteneur-) |
| `reseau-bridge-par-defaut` | Le réseau par défaut, et ce qu'il ne fait pas | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/#le-réseau-bridge--la-fondation) |
| `reseau-bridge-dedie` | Un réseau à soi : nommer et isoler | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/#le-réseau-bridge--la-fondation) |
| `reseau-publication-de-ports` | Publier un port, et seulement où il faut | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/#bonnes-pratiques-réseau) |
| `reseau-interne` | Deux isolations qui ne se ressemblent pas | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/#le-réseau-none--isolation-totale) |
| `reseau-diagnostic-dns` | La boutique ne trouve plus son catalogue | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/#dépannage-réseau-docker) |
| `donnees-volumes-et-montages` | Où les données survivent : les trois types de montage | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/#vue-densemble-des-types-de-volumes) |
| `donnees-permissions-uid-gid` | Deux conteneurs, un volume, des droits qui tiennent | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/#les-volumes-standards) |

### Mesurer l'isolation, et remettre un conteneur en service

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `internes-namespaces` | Un namespace est une vue, pas un mur | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/#namespaces--isoler-ce-que-le-conteneur-voit) |
| `internes-cgroups-v2` | Les cgroups : ce qu'un conteneur peut consommer | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise) |
| `internes-stockage-des-images` | Où atterrissent vraiment les fichiers d'un conteneur | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/) |
| `internes-chaine-dexecution` | Qui lance vraiment un conteneur | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/#comment-ces-mécanismes-fonctionnent-ensemble) |
| `container-limite-cpu` | Brider un processeur, et le prouver | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise) |
| `container-ulimits-et-shm` | La mémoire partagée et les descripteurs | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise) |
| `troubleshoot-exit-127` | Trois pannes, trois codes, une grille | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#décoder-les-exit-codes) |
| `troubleshoot-conflit-de-port` | Deux conflits de port, deux causes | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#checklist-de-debug-réseau) |
| `troubleshoot-permission-refusee` | Trois accès refusés, trois causes | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/#les-volumes-standards) |
| `troubleshoot-boucle-de-redemarrage` | Une boucle de redémarrage, et deux issues | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#restart-policies--redémarrer-automatiquement) |

### Construire ses images

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `images-identifier-image` | Identité d'une image : le tag ment, le digest non | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/) |
| `images-ordre-des-couches` | Le même Dockerfile, et un cache qui sert enfin | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/#principe-1--maximiser-le-cache-avec-lordre-des-instructions) |
| `images-contexte-de-build` | Un fichier qui existe, et qu'on ne trouve pas | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/#principe-2--utiliser-dockerignore) |
| `images-optimiser-la-taille` | Ce qu'une couche garde | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/optimiser-taille-image/) |
| `images-migrer-vers-alpine` | Changer de socle n'est pas changer une ligne | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/optimiser-taille-image/#choisissez-la-bonne-image-de-base) |
| `images-build-multi-etapes` | Ce qui vient du socle ne se retire pas | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/#principe-3--multi-stage-build-pour-des-images-légères) |
| `images-non-root` | USER change l'identité, et aucun droit | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/#principe-4--exécuter-en-non-root) |
| `images-healthcheck` | « Up » ne dit rien du service | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#surveiller-la-santé-avec-healthcheck) |

_32 labs, table générée par `scripts/gen_catalog.py`._
<!-- LABS:END -->

## Où en est ce catalogue

Il est en construction. `ROADMAP.md` porte le backlog complet, organisé par
compétence et par vagues, `COVERAGE.md` la matrice des guides du blog, et
`AUDIT.md` ce que la refonte a repris de l'ancien dépôt et ce qu'elle a jeté.

`validation-labs.json` porte le verdict de chaque lab : il n'y figure que
lorsqu'il a été joué dans les deux sens, score nul avant le travail et plein
après.

## Contribuer

- Contribuer : voir [CONTRIBUTING](./CONTRIBUTING.fr.md).
- Conduite : [Code de conduite](./CODE_OF_CONDUCT.fr.md) · Sécurité : [SECURITY](./SECURITY.fr.md).
- Ce qui a changé, et quand : [CHANGELOG](./CHANGELOG.fr.md).
- Ce qui existait avant ce catalogue : voir plus bas.

Ce catalogue remplace
[containers-training](https://github.com/stephrobert/containers-training), qui
reste en place : ses cinq TP y sont lisibles, et leur substance est reprise ici
sous forme de labs mesurés.

## Licence

Voir [`LICENSE`](./LICENSE) (CC BY 4.0).
