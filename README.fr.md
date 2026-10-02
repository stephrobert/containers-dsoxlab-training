# Labs Conteneurs

**Langue :** [English](./README.md) · [Français](./README.fr.md)

[![Licence : CC BY 4.0](https://img.shields.io/badge/Licence-CC%20BY%204.0-lightgrey.svg)](./LICENSE)

Catalogue de **labs vérifiables** de la formation Conteneurisation du blog
[blog.stephane-robert.info](https://blog.stephane-robert.info/docs/conteneurs/),
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
blog.stephane-robert.info     explique, enseigne
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

Aucun provisionnement n'est nécessaire pour commencer : les labs des premiers
blocs se jouent sur votre machine, avec votre moteur Docker. Les labs qui
exigent une machine dédiée le déclarent, et `dsoxlab provision` s'en occupera
le jour où vous les atteindrez.

## Votre premier lab, en cinq minutes

```bash
export LAB_HOME=$PWD

dsoxlab list-labs                        # ce que le catalogue contient
dsoxlab run       images-premiere-image  # pose le point de départ
dsoxlab challenge images-premiere-image  # la mission
# ... vous travaillez dans challenge/work ...
dsoxlab check     images-premiere-image  # le score
```

## Comment ça marche

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

### Les tests lisent l'état, jamais vos commandes

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

### Les indices ont un coût, et c'est voulu

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
| **Docker** | images, exécution, données, réseau, sécurité, internes | votre moteur, parfois une machine dédiée |
| **Compose** | une application à plusieurs services, décrite et diagnostiquée | votre moteur |
| **Swarm** | un orchestrateur distribué : Raft, quorum, overlay, secrets | plusieurs machines |

Swarm est un **parcours avancé, clairement séparé**. Ce n'est pas une étape
vers Kubernetes dans ce dépôt : c'est un orchestrateur à part entière, avec son
consensus et son état de contrôle à protéger.

## Le catalogue

<!-- LABS:START -->
### Construire des images

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `images-premiere-image` | Première image : l'application voyage en conteneur, et le prouve | c2 | - | shell + Docker | [guide](https://blog.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/) |

_1 labs, table générée par `scripts/gen_catalog.py`._
<!-- LABS:END -->

## Où en est ce catalogue

Il est en construction. `ROADMAP.md` porte le backlog complet, organisé par
compétence et par vagues, `COVERAGE.md` la matrice des guides du blog, et
`AUDIT.md` ce que la refonte a repris de l'ancien dépôt et ce qu'elle a jeté.

`validation-labs.json` porte le verdict de chaque lab : il n'y figure que
lorsqu'il a été joué dans les deux sens, score nul avant le travail et plein
après.

## Contribuer et licence

- Contribuer : voir [CONTRIBUTING](./CONTRIBUTING.fr.md).
- Conduite : [Code de conduite](./CODE_OF_CONDUCT.fr.md) · Sécurité : [SECURITY](./SECURITY.fr.md).
- Ce qui a changé, et quand : [CHANGELOG](./CHANGELOG.fr.md).
- Licence : [CC BY 4.0](./LICENSE).

Ce catalogue remplace
[containers-training](https://github.com/stephrobert/containers-training), qui
reste en place : ses cinq TP y sont lisibles, et leur substance est reprise ici
sous forme de labs mesurés.
