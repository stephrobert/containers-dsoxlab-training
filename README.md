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

No provisioning is needed to start: the labs of the first blocks run on your
own machine, with your Docker engine. Labs that require a dedicated machine
declare it, and `dsoxlab provision` will take care of it the day you reach
them.

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
| `shell` | a terminal and a working Docker daemon. The tests inspect the images, containers and networks that Docker actually holds. |

This catalogue declares no `infra:` block at all: no virtual machine, no
`dsoxlab provision`. Containers are what is being taught, so they run on your
own engine.

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
| **Docker** | images, runtime, data, network, security, internals | your engine, sometimes a dedicated machine |
| **Compose** | a multi-service application, described and diagnosed | your engine |
| **Swarm** | a distributed orchestrator: Raft, quorum, overlay, secrets | several machines |

Swarm is an **advanced, clearly separate path**. It is not a stepping stone to
Kubernetes in this repository: it is an orchestrator in its own right, with its
consensus and its control state to protect.

## The catalogue

<!-- LABS:START -->
### Build images

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `images-identifier-image` | Image identity: the tag lies, the digest does not | c2 | - | vm | [guide](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/) |

_1 labs, table generated by `scripts/gen_catalog.py`._
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
