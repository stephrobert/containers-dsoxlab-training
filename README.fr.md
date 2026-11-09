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

**Vous n'avez pas besoin de savoir programmer** : chaque lab fournit le code
dont il a besoin. Vous travaillez l'image, l'exécution, le réseau, le stockage,
la distribution et le durcissement.

Chaque module se termine par une **épreuve** : cinq contrôles de poids égal, un
seuil de 75 sur 100, quatre indices qui coûtent des points, et une exigence
critique qu'aucun total ne compense. Une épreuve note **l'état final** du
système, jamais les commandes tapées : deux chemins qui aboutissent au même état
reçoivent la même note.

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
| **La VM Docker provisionnée** | tous les labs interrogent son moteur ; Docker n'est pas requis sur le poste |
| **`uv`** | il installe dsoxlab et l'outillage du catalogue |
| **`mise`**, facultatif | il pose hadolint, dive et trivy aux versions épinglées |

`infra/bootstrap.yaml` installe Docker et son outillage dans les VM provisionnées.
Le premier lab vérifie ce socle. Les labs nécessitant plusieurs hôtes simultanés
déclarent des rôles sur leur cible runtime ; la table du catalogue indique
le nombre de VM requis.

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
n'installez donc rien sur votre poste, Docker compris : le provisionnement pose
le moteur dans Debian 13. Comptez quelques
minutes de provisionnement avant le premier lab.

### Votre premier lab, en cinq minutes

```bash
export LAB_HOME=$PWD

dsoxlab list-labs                        # ce que le catalogue contient
dsoxlab provision                       # prépare le socle VM
dsoxlab run       docker-verifier-son-moteur  # pose le point de départ
dsoxlab challenge docker-verifier-son-moteur  # la mission
# ... vous travaillez dans challenge/work ...
dsoxlab check     docker-verifier-son-moteur  # le score
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
| `docker-verifier-son-moteur` | Le moteur fonctionne-t-il vraiment ? Quatre réponses, pas une | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/installation/#comment-vérifier-que-linstallation-est-juste-) |
| `docker-premier-conteneur` | Lancer, arrêter, supprimer : trois verbes qui ne se recouvrent pas | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/cli/#comment-lister-arrêter-et-supprimer-un-conteneur-) |
| `docker-cycle-de-vie` | Le cycle de vie : redémarrer n'est pas recréer | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/cycle-de-vie-et-signaux/) |
| `container-entrypoint-et-cmd` | ENTRYPOINT et CMD : lequel vos arguments remplacent-ils ? | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/cli/#entrypoint-et-cmd--que-remplacent-vos-arguments-) |
| `container-signaux-et-pid-1` | Qui est PID 1 décide si votre conteneur s'arrête ou se fait tuer | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/cycle-de-vie-et-signaux/) |
| `docker-inspecter-un-conteneur` | Interroger un conteneur en marche | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/inspecter-un-conteneur/) |
| `epreuve-mettre-un-service-en-marche` | Rien ne tourne sur ce poste | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/epreuves/mettre-un-service-en-marche/#passer-lépreuve) |
| `docker-anatomie-dune-image` | L'anatomie d'une image : couches, partage, configuration | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/anatomie/) |
| `reseau-bridge-par-defaut` | Le réseau par défaut, et ce qu'il ne fait pas | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/) |
| `reseau-bridge-dedie` | Un réseau à soi : nommer et isoler | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/) |
| `reseau-publication-de-ports` | Publier un port, et seulement où il faut | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/publier-un-port/) |
| `reseau-interne` | Deux isolations qui ne se ressemblent pas | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/reseau-interne/#mettre-en-pratique) |
| `epreuve-exposer-sans-exposer-sa-base` | Exposer une application sans exposer sa base | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/epreuves/relier-deux-conteneurs/#passer-lépreuve) |
| `donnees-volumes-et-montages` | Où les données survivent : les trois types de montage | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/) |
| `donnees-permissions-uid-gid` | Deux conteneurs, un volume, des droits qui tiennent | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/droits-sur-un-volume/) |
| `container-arret-transactionnel` | Terminer une transaction HTTP avant l'arrêt | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/racine-en-lecture-seule/#mettre-en-pratique) |
| `epreuve-remettre-trois-conteneurs-en-service` | Trois conteneurs en panne, trois causes différentes | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/epreuves/remettre-trois-conteneurs-en-service/#passer-lépreuve) |
| `remettre-un-conteneur-en-service` | La boutique ne trouve plus son catalogue | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/epreuves/1-remettre-un-conteneur-en-service/#passer-lépreuve) |

### Mesurer l'isolation, et remettre un conteneur en service

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `internes-namespaces` | Un namespace est une vue, pas un mur | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/) |
| `internes-cgroups-v2` | Les cgroups : ce qu'un conteneur peut consommer | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/) |
| `internes-stockage-des-images` | Où Docker range les fichiers d'un conteneur | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/) |
| `internes-chaine-dexecution` | Qui lance vraiment un conteneur | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/chaine-d-execution/#mettre-en-pratique) |
| `container-limite-cpu` | Brider un processeur, et le prouver | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/brider-un-conteneur/#mettre-en-pratique) |
| `container-ulimits-et-shm` | La mémoire partagée et les descripteurs | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/brider-un-conteneur/#mettre-en-pratique) |
| `troubleshoot-exit-127` | Trois pannes, trois codes de sortie à lire | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#que-signifient-les-codes-125-126-et-127-) |
| `troubleshoot-conflit-de-port` | Deux conflits de port, deux causes | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/publier-un-port/) |
| `troubleshoot-permission-refusee` | Trois accès refusés, trois causes | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/droits-sur-un-volume/) |
| `troubleshoot-boucle-de-redemarrage` | Une boucle de redémarrage, et deux issues | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#comment-arrêter-une-boucle-de-redémarrage-) |
| `epreuve-contenir-un-conteneur-gourmand` | Le traitement qui emporte la machine avec lui | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/epreuves/contenir-un-conteneur-gourmand/#passer-lépreuve) |

### Construire ses images

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `images-identifier-image` | Identité d'une image : le tag ment, le digest non | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/identite-d-une-image/#mettre-en-pratique) |
| `images-ordre-des-couches` | Le même Dockerfile, et un cache qui sert enfin | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/#mettre-en-pratique) |
| `images-contexte-de-build` | Un fichier qui existe, et qu'on ne trouve pas | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/#mettre-en-pratique) |
| `images-optimiser-la-taille` | Ce qu'une couche garde | c5 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/optimiser-taille-image/) |
| `images-migrer-vers-alpine` | Changer de socle n'est pas changer une ligne | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/choisir-une-image-de-base/) |
| `images-build-multi-etapes` | Ce qui vient du socle ne se retire pas | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/build-multi-etapes/#mettre-en-pratique) |
| `images-non-root` | USER change l'identité, et aucun droit | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/utilisateur-et-permissions/) |
| `images-healthcheck` | « Up » ne dit rien du service | c5 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/tester-une-image/#mettre-en-pratique) |
| `images-tester-le-contrat` | Écrire les tests qui refusent une image cassée | c5 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/tester-une-image/#mettre-en-pratique) |
| `buildkit-cache-monte` | Réutiliser les dépendances quand l'étape de build rejoue | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/#mettre-en-pratique) |
| `buildkit-secret-de-build` | Récupérer une dépendance privée sans embarquer le secret de build | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/build/buildkit/#mettre-en-pratique) |
| `images-multi-architecture` | Publier deux architectures et exécuter les deux | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/multi-architecture/#mettre-en-pratique) |
| `epreuve-livrer-une-premiere-image` | Livrer une première image publiable | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/epreuves/livrer-une-premiere-image/#passer-lépreuve) |

### Distribuer ses images

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `registry-tag-push-pull` | Publier une image qu'un autre client peut réellement récupérer | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/registres/docker-hub/#mettre-en-pratique) |
| `registry-tag-contre-digest` | Retrouver la release d'origine après déplacement de son tag | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/registres/docker-hub/#mettre-en-pratique) |
| `images-epingler-par-digest` | Garder le socle approuvé quand son tag change | c5 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/epingler-et-livrer-hors-ligne/#mettre-en-pratique) |
| `registry-locale-tls` | Servir un registre de confiance et tirer sans désactiver TLS | c5 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/registres/distribution/#mettre-en-pratique) |
| `registry-authentification` | Protéger un registre TLS par authentification | c5 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/registres/distribution/#mettre-en-pratique) |
| `registry-droits-minimaux` | Accorder les droits minimaux à un éditeur et un lecteur distinct | c2 | - | 2 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/epreuves/livrer-une-image-utilisable-ailleurs/#quel-entraînement-avant-lépreuve-) |
| `images-exporter-sans-demon` | Exporter une image sans le démon, et garder ce qui doit survivre | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/exporter-sans-demon-avec-skopeo/#mettre-en-pratique) |
| `registry-air-gap` | Livrer une image complète sans son registre d'origine | c5 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/epingler-et-livrer-hors-ligne/#mettre-en-pratique) |
| `epreuve-livrer-une-image` | Livrer une image qu'un client vierge exécute vraiment | c2 | - | 2 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/epreuves/livrer-une-image-utilisable-ailleurs/#passer-lépreuve) |
| `epreuve-reconstruire-une-image-pour-deux-architectures` | Une seule image, quatre exigences, deux architectures | c5 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/epreuves/reconstruire-une-image-pour-deux-architectures/#passer-lépreuve) |

### Décrire une application avec Compose

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `compose-premiere-stack` | Démarrer et recréer une application Compose à deux services | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/#mettre-en-pratique) |
| `compose-resolution-des-variables` | Résoudre les variables Compose sans mélanger les environnements | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/variables-et-environnements/#mettre-en-pratique) |
| `compose-isolation-reseau` | Séparer les réseaux de façade et de données avec Compose | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/reseaux/#mettre-en-pratique) |
| `compose-persistance` | Conserver les données après recréation Compose | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/donnees-persistantes/#mettre-en-pratique) |
| `compose-tache-de-migration` | Conditionner le démarrage à une migration réussie | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/sante-et-ordre-de-demarrage/#mettre-en-pratique) |
| `compose-secrets` | Accorder un secret Compose uniquement à son consommateur | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/secrets/#mettre-en-pratique) |
| `compose-sante-et-dependances` | Attendre la disponibilité, pas seulement un conteneur démarré | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/sante-et-ordre-de-demarrage/#mettre-en-pratique) |
| `compose-ressources` | Faire appliquer les budgets Compose par le moteur | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/ressources-et-redemarrage/#mettre-en-pratique) |
| `compose-plusieurs-environnements` | Déployer des projets Compose de développement et production isolés | c6 | - | 2 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/promouvoir-un-artefact/#mettre-en-pratique) |
| `compose-profils-et-variantes` | Deux variantes d'un même socle, et aucun montage de dev en déploiement | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/variantes-de-deploiement/) |
| `epreuve-fiabiliser-une-stack` | La stack qui ne marche qu'à la deuxième tentative | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/epreuves/fiabiliser-une-stack/#passer-lépreuve) |

### Exploiter une application Compose

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `compose-retour-arriere` | Revenir en arrière, et refuser le retour qui perdrait les données | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/mettre-a-jour-et-revenir-en-arriere/) |
| `compose-correlation-et-saturation` | Corréler une requête métier et attribuer la saturation CPU | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/journaux-et-saturation/#mettre-en-pratique) |
| `compose-sauver-et-restaurer` | Sauvegarder une stack Compose, et la restaurer ailleurs | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/sauvegarder-et-restaurer/) |
| `epreuve-remettre-une-stack-en-service` | Remettre une stack Compose en service | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/epreuves/remettre-une-stack-en-service/#passer-lépreuve) |
| `epreuve-restaurer-une-stack` | Restaurer une stack sur un autre hôte, données comprises | c4 | - | 2 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/epreuves/3-exploiter-et-restaurer-une-stack/#passer-lépreuve) |

### Administrer et durcir un hôte Docker

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `docker-configurer-le-demon` | Configurer les journaux du démon pour qu'ils survivent au redémarrage | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/daemon-config/#mettre-en-pratique) |
| `docker-contexte-ssh` | Administrer une seconde VM avec un contexte Docker SSH | c6 | - | 2 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/daemon-config/#mettre-en-pratique) |
| `docker-rotation-des-journaux` | Faire tourner le journal d'un conteneur | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/journaux-et-espace-disque/#mettre-en-pratique) |
| `docker-mettre-a-jour-le-moteur` | Monter le moteur sans que la passerelle s'en aperçoive | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/mettre-a-jour-le-moteur/#mettre-en-pratique) |
| `securite-groupe-docker` | Retirer un accès Docker qui ne se justifie plus | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/retirer-les-acces-directs/#mettre-en-pratique) |
| `securite-socket-lecture-seule` | Retirer l'accès direct au socket Docker | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/retirer-les-acces-directs/#mettre-en-pratique) |
| `securite-socket-proxy` | Interposer un proxy filtrant devant l'API Docker | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/socket-proxy/) |
| `securite-rootless` | Qualifier un moteur Docker rootless | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/rootless/#mettre-en-pratique) |
| `securite-capabilities` | Rendre à un service la seule capability dont il a besoin | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/securite/#linux-capabilities) |
| `securite-no-new-privileges` | Empêcher les gains de privilèges au runtime | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/securite/#bonnes-pratiques-runtime) |
| `securite-seccomp` | Mesurer un refus seccomp ciblé | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/seccomp-et-apparmor/#mettre-en-pratique) |
| `securite-apparmor` | Écrire une politique AppArmor qui refuse par défaut | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/seccomp-et-apparmor/#mettre-en-pratique) |
| `container-systeme-en-lecture-seule` | Utiliser une racine de conteneur en lecture seule | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/racine-en-lecture-seule/#mettre-en-pratique) |
| `reseau-pare-feu-cible` | Réparer un flux routé sans retirer les protections | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/reseau-et-pare-feu/#mettre-en-pratique) |
| `container-limite-de-processus` | Plafonner le nombre de tâches du conteneur | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/memoire-et-taches/#mettre-en-pratique) |
| `secrets-au-runtime` | Garder un jeton runtime hors de l'environnement | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/secrets/#mettre-en-pratique) |
| `container-memoire-et-oom` | Fixer un plafond mémoire et contenir un OOM | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/memoire-et-taches/#mettre-en-pratique) |
| `troubleshoot-disque-plein` | Récupérer de l'espace dans un sandbox ENOSPC borné | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/journaux-et-espace-disque/#mettre-en-pratique) |
| `donnees-volume-orphelin` | Récupérer les données orphelines et retirer seulement le jetable | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/donnees-orphelines/#mettre-en-pratique) |
| `epreuve-reprendre-un-hote-docker` | Reprendre un hôte Docker que personne n'a suivi | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/epreuves/reprendre-un-hote-docker/#passer-lépreuve) |

### Industrialiser la chaîne de livraison

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `compose-dans-une-ci` | Exécuter Compose dans une CI locale reproductible | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurisation/cicd-images/#mettre-en-pratique) |
| `image-scan-de-vulnerabilites` | Bloquer une image sur un vrai scan hors ligne daté | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurisation/supply-chain-images/#mettre-en-pratique) |
| `images-signature-identite` | Vérifier la signature d'une archive et l'identité de son signataire | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurisation/supply-chain-images/#mettre-en-pratique) |
| `capstone-chaine-complete` | Livrer et rétablir une application isolée de bout en bout | c6 | - | 2 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/epreuves/4-reprendre-un-service-inconnu/#passer-lépreuve) |
| `epreuve-durcir-sans-casser` | Durcir un service sans le casser | c6 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/epreuves/durcir-sans-casser/#passer-lépreuve) |

_93 labs, table générée par `scripts/gen_catalog.py`._
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
