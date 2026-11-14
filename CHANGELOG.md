# Changelog

**Language:** [English](./CHANGELOG.md) · [Français](./CHANGELOG.fr.md)

This log is **dated and versioned**. It was dated only until 2026-10-17, on the
grounds that a lab catalogue promises no compatibility between two of its
states; the twelve catalogues now publish one release each, and this one is no
longer the exception. The date is kept because it says something the version
does not: **when** a lab was proven.

What the date does bring: knowing **when** a lab was proven, with which version
of the Docker engine and in which storage mode. That is what
`validation-labs.json` records lab by lab, and what this log summarises.

---

## [Unreleased]

### Changed

- The README no longer copies the dsoxlab engine documentation (contract,
  lab life cycle): it links to the pages where the engine documents itself
  (dsoxlab#201). The lifecycle table said that `run` copies the starting
  point into `challenge/work` and that `clean` removes the working directory:
  that is the `shell` runtime, and every lab here is `vm`, where `run` plays
  `setup.yaml` on the machine and `clean` plays `cleanup.yaml`. CONTRIBUTING
  now says that `fixtures/` reaches the machine through the lab's own
  `setup.yaml`, since dsoxlab copies nothing for a `vm` lab.

### Added

- **The fourteen exams declare their criteria and the lessons to review.**
  Each exam groups its tests into criteria named after the measured capability
  (`criteria:`, EN labels in `lab.yaml`, FR in `lab.fr.yaml`), each linked to
  the Docker course lessons that teach it (`lessons`). An exam only gives the
  verdict per criterion during `check`; the engine never displays the lessons,
  the site shows them once the result is sent, without naming the failed
  criterion. Briefs, tests, hints and solutions unchanged.

- **`images-tester-le-contrat` (C19, level c5).** The learner writes an external
  test script, `tester-contrat.sh`, that accepts a correct image and refuses
  broken ones of different kinds. What is graded is the script, played against
  an image set: one correct image the learner built from, an older build the
  brief names, and seven broken images the checks build themselves at grading
  time (data directory owned by root, error reported with exit code 0, no check
  of the mandatory variable, process in root, write outside the data directory,
  SIGTERM ignored, counter lost at stop). Six checks of equal weight; every
  refusal only counts if the same script accepts the correct image, so a script
  that always exits 0 or always exits 1 scores zero. Attested in both
  directions on Docker 29.9.2.

- **`docker-mettre-a-jour-le-moteur` (C35c, level c6).** The engine goes from
  29.8.2 to exactly 29.9.2 on a host that serves a witness service. Five checks
  on the final state: the exact version (not the repository candidate 29.9.3),
  the six packages still held, `live-restore` active with the original log
  options kept, the witness never restarted (process, start time, unbroken
  heartbeat counter) and its data intact. The climb is graded, the way back is
  not. The setup puts the engine back to 29.8.2 and the cleanup gives the
  catalogue 29.9.2 back, six packages held, no `daemon.json`.

- **A guard on critical requirements**
  (`tests/test_exigence_critique_declaree.py`, wired to a hook). A promise that
  "no total makes up for" something, written in a brief, must have its
  `exam_blocking_checks` declaration, otherwise the engine does not enforce it
  and the exam passes with its critical requirement failed. It also refuses a
  declared name matching no test, because a renamed test would disarm the
  requirement in silence. It carries a case that tests itself, on a lab built
  to fail.

- **All fourteen exams declare their blocking check.** dsoxlab 0.7.0 enforces
  it: a failure there refuses the exam whatever the total. Measured on all
  fourteen, with only their blocking check failing: all refused; at the same
  score with an ordinary failure: all passed, except the two whose score falls
  below the threshold.

- **Nine end-of-module tests** bring the catalogue to 90 labs, and the number of
  tests to twelve: bring a service into service, connect two containers, bring
  three containers back into service, deliver a first image, make a stack
  reliable, contain a greedy container, take over a Docker host, harden without
  breaking, and rebuild an image for two architectures. Each carries five checks
  of equal weight, a pass mark of 75, four paid hints and one critical
  requirement that no total makes up for. All attested on 2026-11-02 on Docker
  29.9.2, containerd store.
- **A check on version pinning** (`tests/test_paquets_epingles.py`, wired as a
  hook): it requires `infra/bootstrap.yaml` to declare an exact version for the
  five decisive packages, to put them on `hold`, and the version not to be
  copied into any `setup.yaml`. The 75 setups install `docker-ce` with
  `state: present`, and that is deliberate: the value lives in one place only,
  because a value you have to remember to copy always ends up lying. The four
  checks were bench-tested by sabotage, and each fails when it must.

### Changed

- **dsoxlab floor raised to 0.8.0** (CI and pre-commit): `criteria` does not
  exist before, and an older version refuses it.

- **`securite-capabilities` teaches a real exception.** It required
  `NET_BIND_SERVICE`, which does not exist under Docker: measured on Engine
  29.9.2, a container with no capability at all listens on port 80, because the
  engine sets `net.ipv4.ip_unprivileged_port_start=0` in its network namespace.
  The lab now recreates a job launcher that stops at startup when every
  capability is dropped (its `chroot` is refused) and needs exactly one back,
  `SYS_CHROOT`. Three checks: the declared set and no privileged mode, the
  effective mask `0x40000` together with the launcher's own report, and a real
  ownership change that must fail. Same identifier, new title.

- **Three `doc_url`s follow the rewritten lessons.** `secrets-au-runtime`,
  `docker-contexte-ssh` and `docker-configurer-le-demon` now point at the
  `#mettre-en-pratique` section of their page, the form of the other labs of the
  catalogue.

- **The `doc_url` anchor check now has three outcomes instead of two**
  (`scripts/verifier-ancres.py`, with `tests/test_ancres_trois_issues.py` wired
  as a hook). It queries the published site, whereas the truth about a
  `doc_url` lives in the site's source, which this repository's CI cannot
  reach. Measured on 2026-11-03 by crossing the two, link by link, across the
  91 lab `doc_url`s: 41 green, **50 red, of which 44 are correct against the
  source** and 6 point at draft pages. That is **zero real catalogue debt out
  of 50 red**, yet CI was permanently red and pull requests were merged over
  it. A check people merge over no longer checks anything. An unreachable page
  therefore no longer concludes red: it is `unknown` in the sense of
  `dsoxlab doctor`, always printed, never silenced, and `--strict` gives it its
  own exit code (`10`). An anchor that is correct against the source but not
  yet deployed is declared in `scripts/ancres-en-attente.yml`, named, dated and
  justified, rather than tolerated silently. What keeps that file from becoming
  a dumping ground: the check **fails** on an entry that no longer has a
  purpose, either because the anchor now resolves or because no `doc_url`
  carries it any more. Eleven entries at opening, each measured correct against
  the source.

- **`epreuve-exposer-sans-exposer-sa-base` is refocused on its own module.** Four of
  its five checks restated an earlier lesson's lab, and the module's third
  teaching, isolation, was measured nowhere in the catalogue. It now grades
  publishing on a chosen interface, a service **alias** distinct from the
  container name, a network **with no way out**, no published port on the
  database, and the business request getting through despite the isolation.
  New title: "Exam: expose an application without exposing its database".

- **`epreuve-remettre-une-stack-en-service` is rewritten.** It required a
  health probe and a `depends_on: service_completed_successfully`, both taught
  in the next module. The stack becomes a front end and a data service joined
  **by service name**, and the supplied front end retries its upstream:
  start-up order does not matter, so nothing is borrowed from the next module.

- **`compose-secrets` makes the learner perform the rotation.** The check did
  it itself, wrote a fresh token, recreated the services and restored
  everything: the sheet promised to "replace" a secret and nobody replaced
  anything. The lab now lays down the next value, and the check reads the final
  state, including the container's creation date compared with the file's,
  which catches both of the lesson's traps.

- `reseau-diagnostic-dns` becomes `remettre-un-conteneur-en-service`, and
  `compose-capstone` becomes `epreuve-remettre-une-stack-en-service`, which
  moves to `lab_type: challenge` with a pass mark of 75. Both attestations were
  **removed** from the record rather than renamed: it is indexed by identifier,
  and renaming it would pass off as attested a measurement made on another lab.
  Both labs were re-attested under their new names.
- Nineteen `doc_url` repointed at pages and anchors that exist, every target
  verified on the site's disk before writing.
- The promise of a single FastAPI application running through the whole path is
  removed from both `meta` files: the training plan no longer provides for it.

### Fixed

- **255 image references carried a digest without their tag**, across 75 labs
  (`setup.yaml` and `cleanup.yaml`), including **246 `alpine`** pinned to the
  `:latest` digest. They were reproducible yet unreadable: nothing said this was
  **Alpine 3.24.3**, and finding out required a `docker run` on the VM for
  information that belongs in the file. `LABS-A-ECRIRE.md` has required the
  `image:tag@sha256:…` form since 2026-10-29; `tests/test_images_epinglees.py`
  did not check it, because it did `if "@sha256:" in ref: continue` and so
  accepted any digest-bearing reference. Every tag was **measured** with
  `docker buildx imagetools inspect` and carries exactly the digest already
  written: `alpine:3.24.3`, `debian:13`, `debian:13-slim`,
  `hello-world:latest`. **No image changes**, since Docker ignores the tag once
  a digest is present. One reference stays untagged, `cesanta/docker_auth`,
  whose digest no published tag carries and whose line **removes** it rather
  than pulling it: it carries the repository marker with its reason.
- **The pinning check now has two halves, with deliberately different scopes.**
  The one for references *without a digest* stays with `docker pull`, `FROM` and
  `image:`, because elsewhere the image position depends on options and a
  **container** name would be taken for an image. The one for *digest without a
  tag* searches **everywhere**, the `nom@sha256:` form being unambiguous. Tested
  both ways, marker included, and verified able to refuse: removing the tag from
  a single reference in a real lab makes the check reject it, and it goes green
  again once restored.

- **`buildkit-secret-de-build` required twice over that the secret stay out of
  the build context, and no test measured it.** Its three checks inspected the
  image: configuration, history and saved layers; yet a file sitting in the
  context but never `COPY`-ed enters no layer at all. **The requirement was
  therefore invisible, and the learner believed it was graded**: copying
  `depot.token` into `appli/` and passing it through
  `--secret id=depot,src=./depot.token` scored 100. A fourth check now reads the
  context directory, looking for the token in clear text, in base64, and for the
  assembled `Bearer` header in both forms, because a secret copied into a note
  or a helper script does not always appear raw. It also rejects the copied
  credential file, even empty, and **even when excluded by a `.dockerignore`**:
  an exclusion gets forgotten, and the secret then follows the tree. The
  criterion is added to both scenarios' mission list, since a list that
  enumerates what is graded must name it.
- **The `buildkit-secret-de-build` scenario left the learner without `--load`.**
  Measured on 2026-11-03 on `docker.lab`, Engine 29.9.2, containerd store: with
  the `docker-container` builder the scenario suggests, a build without `--load`
  **succeeds**, the image stays absent from the local store, and the following
  `docker run` answers "Unable to find image ... locally" then "pull access
  denied ... may require `docker login`". **In a lab about build secrets, that
  message sends the learner hunting an authentication problem** where an output
  option is missing. The solution itself used `--load` all along, so the
  attestation stayed green. Both scenarios now name the option and say why.

- **`images-multi-architecture` counted the published index entries rather than
  its variants.** Its brief asked for "exactly two distinct Linux variants";
  the test required `len(manifests) == 2`. Measured on 2026-11-03 on Engine
  29.9.2 and Buildx 0.38.1 against a throwaway registry: a
  `--platform linux/amd64,linux/arm64 --push` push that leaves provenance at
  its default produces an index of **four** entries, the two variants plus two
  attestation manifests on `unknown/unknown`, annotated
  `vnd.docker.reference.type=attestation-manifest`; the same push with
  `--provenance=false` produces two. **The lab's solution uses
  `--provenance=false`, so its attestation stayed green while a learner
  following the lesson failed** with "a release needs two distinct manifests"
  right after delivering two: the same masking as the seven
  `terraform-training` labs in July. The test now counts variants, discarding
  an entry on two criteria rather than either one, the annotation stating
  intent and the `unknown` platform stating form. A witness from the same bench
  shows nothing else changes: the amd64 variant digest of the four-entry index
  pulls and inspects identically. Hint 3, which steered towards the assembly
  strategy for 20 points although the lesson only ranks it third, now names the
  simple route first. Lab re-attested VALID on 2026-11-03 on Docker 29.9.2.
  Defect reported by the website session, which was writing the lesson.

- **`epreuve-mettre-un-service-en-marche` no longer grades `docker.socket`.**
  The check could not be passed with what the lesson teaches:
  `docker.service` carries `Requires=docker.socket`, so the socket becomes
  active on its own but stays **disabled**, and `is-enabled` refused the exact
  gesture the lesson shows.

- **`compose-persistance` no longer requires a read-only root**, taught much
  later. It hid in two places, one of them a check running
  `! touch /tmp/unauthorized` that read like a confinement check: measured,
  `/tmp` is 1777 in the image, so that `touch` succeeds under any UID and only
  fails with a read-only root.

- **The "lost data" of `epreuve-remettre-trois-conteneurs-en-service` is really
  lost.** Its report carried only two fixed lines: a scribe destroyed and
  recreated produced an identical file, and the critical requirement measured
  nothing. A random reference is now written into it from the host, and it
  leaves with the container.

- **Five working directories belong to the learner.** They were `root:root`
  with mode 0755, so handing in work required `sudo`: those labs measure Docker
  and Compose, not permission to write a file.

- **Four `doc_url` and four levels** repointed at pages and anchors that exist,
  verified before pointing at them.

- **Every mention of an AI tool removed** from the commits a learner sees in
  `git log`, in two labs rather than one.

- `container-ulimits-et-shm`: both scenarios announced **1024** descriptors
  where the check requires **256**. Anyone following the brief failed, while the
  attestation stayed green since the solution set 256. And the whole discourse
  about a value "surprisingly large" was a leftover from Docker 26: measured on
  29.9.2, `ulimit -n` is 1024, and it is the gap with the 524288 hard ceiling
  that is instructive.
- `internes-cgroups-v2`, `container-limite-cpu` and `container-ulimits-et-shm`
  claimed you have to be root to read a container's cgroup files. Measured from
  an ordinary account without `sudo`: all six files read, zero refusals.
  **Writing** them does require a privilege, and that is what separates
  observing from tuning.
- `registry-tag-contre-digest` opposed "the manifest digest" and "the
  configuration ID" as two distinct identities. Measured on 29.9.2, containerd
  store: `.Id` is the pushed digest, and the manifest served is an OCI index
  with no configuration key. The brief asked to avoid a value that does not
  exist and happens to be the right one; what is checked is the startup
  reference.
- Nine assertion messages in the new tests become bilingual, and a missing
  bare-tag marker is placed on the second task of `images-identifier-image`.

### Measured

- **a `prune` without `-a` does not remove a NAMED volume**: `docker volume
  prune` and `docker system prune --volumes` leave an unmounted named volume
  intact, and only `docker volume prune -a` removes it. The engine says so
  itself in its warning, "anonymous" without `-a`, "all" with it. Three texts
  named the wrong command;

- **Compose 5.6.1 applies `deploy.resources.limits.memory`**: this form and
  `mem_limit` both give `HostConfig.Memory = 67108864` for 64M, confirmed by
  the cgroup. Two hints claimed the opposite;

- **the default builder builds and pushes multi-platform**: a four-manifest
  index published from the `docker` driver, with no dedicated builder. One hint
  required one;

- **a container on an internal network has no default route**, where an
  ordinary container has one, and both the name and the alias still resolve
  there. A container attached to both networks keeps its route and resolves the
  alias: without that fact the refocused exam would be unplayable;

- **`docker cp` works both ways on a stopped container**, and the copied file
  survives its start.

Facts established on Docker 29.9.2, containerd store, which changed the design
of several labs:

- **dangling images no longer exist**: three builds on the same tag then
  removing the tag leave zero dangling images, an image without a reference
  being collected at once;
- **`docker kill` does not trigger the restart policy**: a container under
  `unless-stopped` stays `exited`, counter at zero, over ten readings in thirty
  seconds. The kernel also protects a namespace's PID 1 against a `kill -9` sent
  from inside it;
- **`NET_BIND_SERVICE` is useless in a container**: the daemon sets
  `net.ipv4.ip_unprivileged_port_start = 0` there, so a container with no
  capability at all listens on port 80;
- **`docker run --platform` does not honour the platform** if a local image
  already matches the reference: an explicit `docker pull --platform` is needed,
  without which the other architecture is never executed;
- **an index published by buildx carries four manifests, not two**, because of
  the provenance attestations, which appear as `unknown` platforms;
- **`--build-arg` leaves a secret in the history** (two occurrences) where
  `--mount=type=secret` leaves none, neither in the history nor in the layers;
- **the `registry:3.1.2` image declares a `VOLUME`**: each registry container
  creates an anonymous volume, and `docker rm` without `-v` leaves it behind.

### Added

- Six labs extend the catalogue to 77: transactional shutdown,
  AMD64/ARM64 execution (VM-local QEMU for ARM64), TLS registry ACLs,
  trusted signing identity, correlated CPU saturation and targeted firewall
  repair. Their placement follows the ordered pedagogical catalogue.
- Data-preserving beginner diagnostics and transactional shutdown follow
  volumes and UID/GID permissions. Persistence trials now retain non-root
  ownership and refused access after recreation; bounded CPU, OOM and
  process-limit trials preserve fresh application receipts.
- A second VM supports fresh-client pulls, application restoration and
  promotion of one artifact without rebuilding. The VM bootstrap installs
  the Docker baseline; runtime roles are replayed and photographed together.
- Strict `--double-passage` validation requires `0/full/0/full/clean`.
  Selective ledger rereading respects `--lab`; historical attestations do
  not count as strict second-passage evidence.

- Nine completed labs on `chantier/labs-restants`: `buildkit-cache-monte`,
  `buildkit-secret-de-build`, `registry-tag-push-pull`,
  `registry-tag-contre-digest`, `images-epingler-par-digest`,
  `registry-locale-tls`, `registry-authentification`, `registry-air-gap`
  and `compose-premiere-stack`, with bilingual challenges and hints,
  encrypted reference solutions and runtime attestations.
- Registry trust is verified through actual CA-removal failures. Offline
  delivery checks reject missing layers even with a warm Docker cache and
  a recalculated checksum. Compose checks force-recreate both services.
- Eight more completed Compose labs cover variable resolution, network
  isolation, persistence, one-shot migration, secrets, health dependencies,
  resource budgets and multiple environments. Each has bilingual material,
  an encrypted solution and a measured 0 → 100 → 0 VM cycle.
  Trials verify direct-IP isolation, fresh persistent writes, failed-job and
  never-ready startup gating, token rotation, effective cgroup controls and
  independent environment recreation.
- Seven completed administration and security labs cover Docker daemon defaults,
  SSH contexts, per-container log rotation, Docker-group privilege removal,
  rootless mode, unsafe socket mounts and a least-privilege API proxy. Each has
  bilingual learner material, an encrypted solution and a clean VM attestation.
- The PostgreSQL backup lab now has an encrypted reference solution and tests
  that independently restore a custom-format dump and compare the actual rows.
- All 71 catalog labs now have a `VALIDE` verdict in `validation-labs.json`;
  the final capstone and updated socket-proxy revisions passed their VM cycles.

### Fixed

- VM lab validation now snapshots Docker over SSH on the actual target,
  including orphaned image IDs, instead of inspecting the workstation.
  Cleanup also rejects deletion of pre-existing objects. New labs remove
  their labeled intermediate images without globally pruning other work.
  Earlier attestations must be rerun before claiming this stronger guarantee.

## [0.2.3] - 2026-10-23

### Added

- A verdict can no longer be committed together with what it measures. The
  `verdicts-et-commun-separes` hook refuses a commit carrying
  `validation-labs.json` alongside anything the cycle plays:
  `challenge/tests/`, `setup.yaml`, `cleanup.yaml`, `lab.yaml` of any lab, and
  the shared tooling. It is itself tested, in both directions, by a hook of its
  own.

  This closes a case **no measurement can catch afterwards**. The staleness of
  a verdict used to be judged by comparing DATES, and that comparison was wrong
  in both directions on 2026-10-22: a correction committed together with the
  verdicts it invalidated passed as healthy, and labs re-attested on a branch
  came back "to be re-attested" after their squash merge, their content
  unchanged. When a squashed pull request touches a test *after* its campaign,
  the single commit carries both and the squash has destroyed what told them
  apart. It cannot be observed, so it is prevented.

  The statement stays allowed next to a verdict: it is not played by the cycle,
  and forbidding it would demand a campaign for a typo.

### Fixed

- `pipelineMustNotLeakSecretsInConfig` is removed from `.plumber.yaml`, where
  it was declared twice. Plumber dropped that control and answers "was removed
  and is now ignored: secret detection is no longer part of Plumber; remove
  this block". Keeping it suggested that secret detection was covered here. It
  is not, and `detect-private-key` is what comes closest, as a hook.

## [0.2.2] - 2026-10-19

### Security

- **The trainer solution is encrypted with ansible-vault.** The `Dockerfile`
  of `images-premiere-image` was committed in plaintext, in a public
  repository: anyone cloning had the answer to the first lab at hand. The
  other catalogues encrypt theirs; this one did not.

  It also slipped past the check, which was worth fixing upstream:
  `dsoxlab validate-structure` only looked at six extensions (`.yaml`, `.yml`,
  `.sh`, `.py`, `.bash`, `.txt`), so a file named `Dockerfile` was never even
  opened. As of 0.5.4 the engine checks every text file in a solution
  directory.

  `scripts/valider-labs.py` lays the solution over the working directory file
  by file: it now **decrypts as it lays**, through
  `scripts/lecture_solution.py`. Otherwise `docker build` would have read
  "$ANSIBLE_VAULT;1.1;AES256" as an instruction, and its error would have
  spoken of Dockerfile syntax rather than encryption.

  Verified on behaviour: laying the solution returns the original Dockerfile
  byte for byte, SHA256 compared before and after. The repository's 31 tests
  pass and `validate-structure` is green.

- **`scripts/hooks/hadolint-cible.sh` decrypts before scanning.** It was the
  second reader of that file, and the quieter one: hadolint would read the
  vault header and its hex blob without seeing a single instruction, so it
  would report green without having checked anything. It now scans a decrypted
  copy whose name keeps the original path, so its messages stay readable.

  In CI, `.vault-pass` does not exist, and that is the convention across the
  whole collection: no catalogue entrusts its secret to the forge. The check
  therefore declares itself **not run**, through a warning visible in the UI,
  instead of passing for a success. It runs on the trainer's machine, where
  the secret lives. That is the accepted cost of encryption, and it was worth
  writing down rather than discovering.

  Both paths were exercised rather than assumed: with the secret, hadolint
  scans the Dockerfile and reports its `DL3008`; without it, the script warns
  and exits 0.

- **The "0 before, 100 after" replay no longer runs in CI, and that is the
  accepted cost of encryption.** The cycle lays the trainer solution over the
  working directory, so it needs the plaintext, and `.vault-pass` is not on
  the forge. Both affected steps therefore declare themselves not run, through
  a visible warning, rather than passing for a success.

  What is lost is real and deserves naming: the standing of
  `validation-labs.json` no longer rests on this CI but on the local campaign
  that produced it. That is now the situation of the eleven other catalogues
  in the collection, none of whose CI replays a lab. The committed record
  holds `images-premiere-image → VALIDE` as of 2026-10-01, and that is the
  proof.

  The other option existed and was set aside: entrusting `.vault-pass` to a
  repository secret would have kept the replay, at the price of putting on the
  forge the secret no catalogue puts there.

## [0.2.1] - 2026-10-19

### Changed

- **Every `doc_url` now points at `www.stephane-robert.info`.** The site moved
  from `blog.` to `www.`, and the old host redirects with a 301 to the same
  path. Nothing was broken: `validate-structure --check-urls` follows
  redirections, and this catalogue was green before a single line changed. The
  migration is housekeeping, not repair: a `doc_url` should point at the page
  rather than depend on a redirection that will be removed one day.

  The paths are identical between the two hosts, so only the host changed. The
  359 `doc_url` the catalogues declare were looked up in the site's own
  repository, offline: all of them exist there, including twenty-three pages
  the old host answered with a 404.

## 2026-10-01

This repository is born today, and it supersedes
[containers-training](https://github.com/stephrobert/containers-training), which
stays in place with its 168 stars and 47 forks.

### Kubernetes leaves the catalogue

`03-Kubernetes/` is removed entirely: Kubernetes lives in
`kubernetes-dsoxlab-training`, with its CKA, CKAD and CKS labs on a real kubeadm
cluster. Two competing courses on one subject diverge.

`01-Docker-compose/` and `02-Docker-swarm/` go too. They held nothing but a
`.gitkeep`, while the README announced them as content. They will come back as
real teaching blocks.

### The five hands-on guides become measured labs

The 1101 lines of walkthrough disappear. They taught, and taught well, but they
measured nothing: a learner copying the blocks reached the result without any
check telling understood work from copied work.

What is kept: the FastAPI application, which becomes the catalogue's **through
line**, and the progression across four successive images. What is thrown away:
the text, which doubled the blog, and three false statements.

`AUDIT.md` documents them, measurement in hand. The three heaviest:

- "The Alpine image currently has no vulnerabilities!", followed by "Check the
  image's security with Trivy". A scan says what its database knows, at that
  moment, of the packages it could identify;
- "Non-root user (optional)", the only `USER` in all five guides;
- an NFS volume on `127.0.0.1`, in an "optional" step that assumes a server
  nothing installs.

A fourth defect was not suspected: `COPY app/` came before the dependency
install, so one line of Python invalidated the most expensive layer.

### The first lab, proven in both directions

`images-premiere-image` carries seven checks, and the last is the one that
matters: it runs the image with `--network none` and requires it to answer
anyway. An image that installs its dependencies at startup passes the other six
and fails there, as it would fail for an offline learner.

```
before the work: 0/7
after the solution: 7/7
after clean and run: 0/7
engine left intact
VALIDE
```

The application's dependencies are **pinned and dated**:
`fastapi==0.142.2`, `uvicorn[standard]==0.54.0`, measured on PyPI that day. The
original guide did not pin them, and the same image rebuilt in six months would
no longer have carried the same code.

### Two measurements that changed the design

**The same image measures 83 MiB through the API and 329 MiB through
`docker images`.** A factor of four, because the engine uses the containerd
image store: the API returns the compressed size, the registry's, and the
command the on-disk one.

Three of the five labs to port are optimisation labs. A threshold in bytes
written into a test would therefore be incomprehensible, since the learner reads
the other figure in their terminal. `conftest.py` exposes both readings, and the
labs compare **ratios** between images measured the same way.

**An anchor is accepted in `doc_url`**, which makes precise pairing workable
where the guides are dense: 1095 lines of Swarm guide for 18 planned labs, 798
for the 12 Compose labs.

But the blog's slug rule cannot be guessed. A first slugger was right 26 times
out of 68. The real rule keeps accents and strips punctuation without a
separator:

```text
'Prérequis'                     -> #prérequis
"Initialisation d'un cluster"   -> #initialisation-dun-cluster
"Qu'est-ce que Docker Swarm ?"  -> #quest-ce-que-docker-swarm-
'Exemple : workers uniquement'  -> #exemple--workers-uniquement
```

Corrected, it is right **114 times out of 114**.

### The checker that caught 44 errors

`scripts/verifier-ancres.py`, written to check the backlog, showed that **44 of
the 64 anchors drafted were wrong**: those taken from the blog's inventory were
right, those written from memory were invented, and nothing told them apart on
reading.

`validate-structure --check-urls` does not see this defect: it checks the page's
HTTP status, not the fragment.

### Analysis before code

`AUDIT.md`, `COVERAGE.md` and `ROADMAP.md` ship before writing labs in series.
They say, figures in hand: 42 guides in scope, 525 sections, 16 quizzes already
online, and **three gaps** the former repository left wide open.

| Skill | Guides available | Labs before |
| --- | --- | --- |
| distributing images | 7 guides, 2 505 lines | none |
| operating and debugging | 3 guides, 2 176 lines | none |
| hardening | 3 guides, 1 896 lines | none |

The backlog holds **89 labs**, in six waves, the second of which is entirely
playable without provisioning a machine.

### The technical foundation

`meta.yml` on dsoxlab 0.3.0's v1 contract, organised **by skill** rather than by
feature. `conftest.py` with the Docker primitives. Sixteen pre-commit hooks,
four catalogue checkers, and a validator that photographs the engine before and
after every lab.

The licence moves from CC BY-SA 4.0 to **CC BY 4.0**, like the three other
catalogues, official text bare: a `LICENSE` preceded by a header box is not
detected by GitHub.

`mise.toml` pins hadolint, dive, trivy and uv. **Docker is not there**:
`mise ls-remote docker` returns nothing, and rightly so. A daemon with its
service, its group and its socket is not installed by dropping a binary. The
catalogue **checks for it** instead of installing it.

## [0.2.0] - 2026-10-17

### Changed

- **The validator reads the contract, not the terminal panel.**
  `scripts/valider-labs.py` parsed the score out of what `dsoxlab check`
  *displays*. That panel is interface: it changed in dsoxlab 0.4.0 and the
  regex stopped finding anything. It now reads `check --json`, which carries a
  `schema`, and the reading lives in `scripts/verdict_check.py`, **identical in
  all twelve catalogs**.

- **Three verdicts, not two.** A run where every collected test skipped
  measured nothing: it is **SKIP**, neither green nor red, and it stays to be
  measured. Painting it red would accuse the lab of what is missing from the
  machine. `--check` therefore exits `10` in that case, against `1` for a RED,
  mirroring `dsoxlab doctor --strict` where 9 is repaired and 10 is remeasured.

- **The README takes the reference structure** shared by the twelve catalogs:
  fourteen sections, in both languages. Seven of them describe dsoxlab rather
  than the subject, and are therefore identical everywhere.

### Requires

- **dsoxlab 0.4.1 or later**, which introduced the `status` field of
  `check --json`. Without it the validator refuses to conclude rather than
  guessing.
