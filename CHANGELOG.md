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
