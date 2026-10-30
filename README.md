# Container labs

**Language:** [English](./README.md) · [Français](./README.fr.md)

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](./LICENSE)

A catalogue of **verifiable labs** for the Containers course on
[www.stephane-robert.info](https://www.stephane-robert.info/docs/conteneurs/),
driven by the [dsoxlab](https://github.com/stephrobert/dsoxlab) CLI.

## What it is

A set of exercises that **measure** what you can do. Each lab lays down a
starting state, gives you a situation, and checks the result by querying the
Docker engine: the image built, its size, the user running it, the container's
mounts, what the application answers.

A single FastAPI application runs through the whole path and becomes
progressively more correct. **You do not need to know how to program**: the
code is given. You work on the image, the runtime, the network, storage,
distribution and hardening.

## What it is not

**It is not a course.** The courses live on the blog, and this repository does
not rewrite them:

```text
www.stephane-robert.info     explains, teaches
this repository               makes you practise, measures, proves
```

Every lab carries a `doc_url` to the lesson it proves, anchored on the exact
section. If a lab resists you, the lesson is one click away.

**It is not a Kubernetes course.** Kubernetes has its own catalogue,
[kubernetes-dsoxlab-training](https://github.com/stephrobert/kubernetes-dsoxlab-training),
with CKA, CKAD and CKS labs on a real kubeadm cluster. Nothing here mentions
`kubectl`, Helm or manifests.

**It is not a full DevSecOps course.** Trivy, Cosign, GitHub Actions and GitLab
CI appear when a container skill calls for them, and no further: they have
their own guides.

## Requirements

| What you need | Why |
| --- | --- |
| **A Docker engine that answers** | every lab queries it. `docker info` must succeed |
| **`uv`** | it installs dsoxlab and the catalogue's tooling |
| **`mise`**, optional | it provides hadolint, dive and trivy at pinned versions |

This catalogue does not install Docker: it is a daemon, with a service, a user
group and a socket. The blog has a guide for that, and the first lab of the
path makes checking it its subject.

## Install

```bash
# 1. dsoxlab, the tool that runs the labs
uv tool install dsoxlab

# 2. this catalogue
git clone https://github.com/stephrobert/containers-dsoxlab-training.git
cd containers-dsoxlab-training

# 3. the pinned tooling, optional but recommended
mise install
```

Every lab runs inside a **throwaway virtual machine**, which
`dsoxlab provision` brings up for you and `dsoxlab destroy` removes. You
install nothing on your own machine, Docker included: the lab installs the
engine, in a Debian 13 that does not outlive the session. Allow a few minutes
of provisioning before the first lab.

### Your first lab, in five minutes

```bash
export LAB_HOME=$PWD

dsoxlab list-labs                        # what the catalogue holds
dsoxlab run       images-premiere-image  # lay down the starting point
dsoxlab challenge images-premiere-image  # the mission
# ... you work in challenge/work ...
dsoxlab check     images-premiere-image  # the score
```

### Keeping it up to date

```bash
uv tool upgrade dsoxlab        # the engine, published on PyPI
git -C <this repo> pull        # the catalogue
```

The engine and the catalogue move independently: a new `dsoxlab` never requires
re-cloning the labs, and new labs never require upgrading the tool, as long as
the contract version matches.

## How it works

### The declarative contract (two levels)

The catalogue is described by data, not code, which is what keeps the `dsoxlab`
engine domain-agnostic:

- **`meta.yml`** at the root declares the repository identity and the **order**
  of the eight sections shown by `list-labs`, which carry the ids of the
  course modules, plus the Swarm path declared outside the course;
- **`lab.yaml`** per lab declares its `skills`, `level`, `runtime` (type,
  fixtures, services), `distros`, `doc_url` and a `validation` block. A
  `lab.fr.yaml` overrides `title` and `description` in French, and nothing else.

`dsoxlab validate-structure` checks the whole contract, and the sections
declared in `meta.yml` with no lab yet are exactly how this catalogue states
what it still owes.

### The lab lifecycle

| Command | What it does |
| --- | --- |
| `dsoxlab list-labs` | the catalogue, in teaching order |
| `dsoxlab run <id>` | copies the starting point into `challenge/work` |
| `dsoxlab challenge <id>` | the mission: what to reach, not how |
| `dsoxlab check <id>` | runs the tests and returns a score out of 100 |
| `dsoxlab hint <id>` | one hint, at a cost deducted from the score |
| `dsoxlab submit <id>` | records the result for good |
| `dsoxlab progress` | where you stand, lab by lab |
| `dsoxlab clean <id>` | removes the working directory |

### Runtimes

| Runtime | What the lab asks for |
|---|---|
| `vm` | a throwaway Debian 13, brought up by `dsoxlab provision` and torn down by `dsoxlab destroy`. The lab installs Docker there; the tests inspect the images, containers and networks that this engine actually holds. |

**You do not install Docker on your own machine.** That is a decision of this
catalogue, taken on 2026-10-28: a virtual machine is thrown away, whereas a
Docker daemon left on your working machine stays, with its `docker` group, its
service and its images. The labs therefore cost you a `dsoxlab provision` of a
few minutes, and nothing else.

In exchange they can teach what a container on your own machine could not: the
daemon configuration, rootless mode, seccomp, AppArmor, the firewall, a
registry with its certificate. And a lab that fills the disk on purpose fills
its own.

### The validation model

**The tests read state, never your commands.**

You reach the result by whatever path you like. A test in this catalogue looks
like this:

```python
assert inspecter_image(tag)["Config"]["ExposedPorts"]   # what the image declares
code, body = conteneur.repondre("/health")              # what the application returns
assert conteneur.utilisateur() != "0"                   # who actually runs it
```

And never like this:

```python
assert "docker build" in history   # which proves nothing
```

### Scoring, hints, progress

**Hints cost points, and that is deliberate.**

Four hints per lab, from the vaguest to the most explicit. Each one costs. The
last names the tool that shows the fault when everything looks right without
being right, but none gives the Dockerfile away.

### Three levels of exercise

| Type | What you get |
| --- | --- |
| `lab` | an explanation and a focused mission |
| `challenge` | an objective and constraints, no recipe |
| `capstone` | a real situation, and the problem is not announced |

You progressively lose the guidance. That is the point of the path.

## Docker, Compose, Swarm: three distinct blocks

| Block | What it teaches | What it requires |
| --- | --- | --- |
| **Docker** | images, runtime, data, network, security, internals | a throwaway VM |
| **Compose** | a multi-service application, described and diagnosed | the same VM |
| **Swarm** | a distributed orchestrator: Raft, quorum, overlay, secrets | several VMs |

Swarm is an **advanced, clearly separate path**. It is not a stepping stone to
Kubernetes in this repository: it is an orchestrator in its own right, with its
consensus and its control state to protect.

## The catalogue

<!-- LABS:START -->
### Use containers

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `docker-verifier-son-moteur` | Is the engine actually working? Four answers, not one | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/installation/#vérification-de-linstallation) |
| `docker-premier-conteneur` | Run, stop, remove: three verbs that do not overlap | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/cli/#lancer-et-gérer-les-conteneurs-docker) |
| `docker-cycle-de-vie` | The life cycle: restarting is not recreating | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/concepts/#cycle-de-vie-dun-conteneur) |
| `container-entrypoint-et-cmd` | ENTRYPOINT and CMD: which one do your arguments replace? | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#le-cycle-de-vie-dun-conteneur) |
| `container-signaux-et-pid-1` | Who is PID 1 decides whether your container stops or gets killed | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#stop-vs-kill--quelle-différence-) |
| `docker-inspecter-un-conteneur` | Interrogate a running container | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#les-commandes-indispensables) |
| `docker-anatomie-dune-image` | The anatomy of an image: layers, sharing, configuration | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/#comment-est-construite-une-image-de-conteneur-) |
| `reseau-bridge-par-defaut` | The default network, and what it does not do | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/#le-réseau-bridge--la-fondation) |
| `reseau-bridge-dedie` | A network of your own: naming and isolating | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/#le-réseau-bridge--la-fondation) |
| `reseau-publication-de-ports` | Publishing a port, and only where it belongs | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/#bonnes-pratiques-réseau) |
| `reseau-interne` | Two isolations that are not alike | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/#le-réseau-none--isolation-totale) |
| `reseau-diagnostic-dns` | The shop cannot find its catalogue | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/#dépannage-réseau-docker) |
| `donnees-volumes-et-montages` | Where data survives: the three kinds of mount | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/#vue-densemble-des-types-de-volumes) |
| `donnees-permissions-uid-gid` | Two containers, one volume, rights that hold | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/#les-volumes-standards) |

### Measure isolation, and put a container back in service

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `internes-namespaces` | À remplir | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/#namespaces--isoler-ce-que-le-conteneur-voit) |
| `internes-cgroups-v2` | À remplir | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise) |
| `internes-stockage-des-images` | À remplir | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/) |
| `internes-chaine-dexecution` | À remplir | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/#comment-ces-mécanismes-fonctionnent-ensemble) |
| `container-limite-cpu` | À remplir | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise) |
| `container-ulimits-et-shm` | À remplir | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/#cgroups--limiter-ce-que-le-conteneur-utilise) |
| `troubleshoot-exit-127` | À remplir | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#décoder-les-exit-codes) |
| `troubleshoot-conflit-de-port` | À remplir | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#checklist-de-debug-réseau) |
| `troubleshoot-permission-refusee` | À remplir | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/#les-volumes-standards) |
| `troubleshoot-boucle-de-redemarrage` | À remplir | c1 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#restart-policies--redémarrer-automatiquement) |

### Build images

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `images-identifier-image` | Image identity: the tag lies, the digest does not | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/) |
| `images-ordre-des-couches` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/#principe-1--maximiser-le-cache-avec-lordre-des-instructions) |
| `images-contexte-de-build` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/#principe-2--utiliser-dockerignore) |
| `images-optimiser-la-taille` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/optimiser-taille-image/) |
| `images-migrer-vers-alpine` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/optimiser-taille-image/#choisissez-la-bonne-image-de-base) |
| `images-build-multi-etapes` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/#principe-3--multi-stage-build-pour-des-images-légères) |
| `images-non-root` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/#principe-4--exécuter-en-non-root) |
| `images-healthcheck` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#surveiller-la-santé-avec-healthcheck) |
| `buildkit-cache-monte` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/build/buildkit/#cache-avancé) |
| `buildkit-secret-de-build` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/secrets/#buildkit--secrets-au-moment-du-build) |

### Distribute images

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `registry-tag-push-pull` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/registres/#docker-push--envoyer-une-image-vers-la-registry) |
| `registry-tag-contre-digest` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/registres/#tags-vs-digests--la-distinction-critique) |
| `images-epingler-par-digest` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/registres/#tags-vs-digests--la-distinction-critique) |
| `registry-locale-tls` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/registres/distribution/#configurer-tls) |
| `registry-authentification` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/registres/distribution/#configurer-lauthentification) |
| `registry-air-gap` | À remplir | c2 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/outils/skopeo/#environnements-air-gap-déconnectés) |

### Describe an application with Compose

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `compose-premiere-stack` | À remplir | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/#votre-premier-composeyaml) |
| `compose-resolution-des-variables` | À remplir | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/#configuration-avancée) |
| `compose-isolation-reseau` | À remplir | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/#concepts-clés) |
| `compose-persistance` | À remplir | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/#concepts-clés) |
| `compose-tache-de-migration` | À remplir | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/#configuration-avancée) |
| `compose-secrets` | À remplir | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/#configuration-avancée) |
| `compose-sante-et-dependances` | À remplir | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/#configuration-avancée) |
| `compose-ressources` | À remplir | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/#configuration-avancée) |
| `compose-plusieurs-environnements` | À remplir | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/#configuration-avancée) |

### Operate a Compose application

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `donnees-postgres-sauvegarde` | À remplir | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/#sauvegarderestauration-des-volumes-docker) |
| `compose-capstone` | À remplir | c3 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/) |

### Administer and harden a Docker host

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `docker-configurer-le-demon` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/daemon-config/) |
| `docker-contexte-ssh` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/daemon-config/#structure-et-syntaxe) |
| `docker-rotation-des-journaux` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/daemon-config/#logging-drivers) |
| `securite-groupe-docker` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/securite/#comprendre-le-modèle-de-menaces-docker) |
| `securite-socket-lecture-seule` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/socket-proxy/#pourquoi-ro-ne-suffit-pas) |
| `securite-socket-proxy` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/socket-proxy/) |
| `securite-rootless` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/securite/#rootless-mode) |
| `securite-capabilities` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/#capabilities--fragmenter-les-privilèges-root) |
| `securite-no-new-privileges` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/securite/#bonnes-pratiques-runtime) |
| `securite-seccomp` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/securite/#profils-seccomp) |
| `securite-apparmor` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/securite/#apparmor-et-selinux) |
| `container-systeme-en-lecture-seule` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/securite/#bonnes-pratiques-runtime) |
| `container-limite-de-processus` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/securite/#bonnes-pratiques-runtime) |
| `secrets-au-runtime` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/secrets/#injection-au-runtime--autres-méthodes) |
| `container-memoire-et-oom` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/execution-depannage/#diagnostic-approfondi--le-cas-oom-kill) |
| `troubleshoot-disque-plein` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/daemon-config/#optimisations-production) |
| `donnees-volume-orphelin` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/volumes/#bonnes-pratiques-de-gestion-des-volumes) |

### Industrialise the delivery chain

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `compose-dans-une-ci` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/#commandes-essentielles) |
| `image-scan-de-vulnerabilites` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/registres/quay-io/#publier-une-image-sur-quayio) |
| `capstone-chaine-complete` | À remplir | c4 | - | 1 VM | [guide](https://www.stephane-robert.info/docs/conteneurs/-) |

_71 labs, table generated by `scripts/gen_catalog.py`._
<!-- LABS:END -->

## Where this catalogue stands

It is under construction. `ROADMAP.md` holds the full backlog, organised by
skill and in waves, `COVERAGE.md` the matrix of the blog's guides, and
`AUDIT.md` what the rebuild kept from the former repository and what it threw
away.

`validation-labs.json` holds each lab's verdict: a lab appears there only once
it has been played in both directions, scoring zero before the work and full
marks after.

## Contributing

- Contributing: see [CONTRIBUTING](./CONTRIBUTING.md).
- Conduct: [Code of Conduct](./CODE_OF_CONDUCT.md) · Security: [SECURITY](./SECURITY.md).
- What changed, and when: [CHANGELOG](./CHANGELOG.md).
- What changed before this catalogue: see below.

This catalogue supersedes
[containers-training](https://github.com/stephrobert/containers-training), which
stays in place: its five hands-on guides remain readable there, and their
substance is carried over here as measured labs.

## License

See [`LICENSE`](./LICENSE) (CC BY 4.0).
