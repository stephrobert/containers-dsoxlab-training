# Contributing

**Language:** [English](./CONTRIBUTING.md) · [Français](./CONTRIBUTING.fr.md)

Thank you for wanting to improve this catalogue. This document says what a lab
must carry, and above all **what gets a contribution refused**, so you do not
learn it after writing one.

## The rule that governs everything else

> A passing test proves nothing until you have seen what must fail actually
> fail.

A lab is measured in both directions: **zero** before the work, **full marks**
after. A lab that awards points before anything is done does not measure a
skill, it measures its own starting state.

```bash
dsoxlab run   <id>    # the starting point is laid down
dsoxlab check <id>    # MUST return 0
# then the reference solution, in challenge/work
dsoxlab check <id>    # MUST return 100
```

`scripts/valider-labs.py` runs that cycle, and more: it photographs the Docker
engine before and after, and an image, a volume, a container or a network left
behind makes the lab **ROUGE**. That is not zeal: the next lab would pay for it,
by finding a state it did not create.

```bash
python3 scripts/valider-labs.py --lab <id>
```

## What your lab must carry

| File | Role |
| --- | --- |
| `lab.yaml` | the contract: `level` = the skill, `doc_url` = the **anchored** lesson |
| `lab.fr.yaml` | `title` and `description` in French, and **nothing else** |
| `scenario.md`, `.fr.md` | the **situation** and the objective, never a walkthrough |
| `README.md`, `.fr.md` | the tutorial: the mechanism, on throwaway examples |
| `challenge/README.md`, `.fr.md` | the **brief**, as numbered requirements |
| `challenge/hints.yaml` | four base64 hints, bilingual, at increasing cost |
| `challenge/tests/test_functional.py` | the proof. The name is set by the contract |
| `fixtures/` | the starting point, copied into `challenge/work` by `dsoxlab run` |
| `solution/` | the reference solution, laid on top for validation |

A fixture **declared** in `lab.yaml` must exist in `fixtures/`, and a fixture
present but not declared is **not** copied. The first case is refused by
`dsoxlab validate-structure`; the second leaves an incomplete working directory
without any message saying so.

## What gets a contribution refused

### A test reading commands instead of state

```python
# NO
assert "docker build" in history

# YES
assert inspecter_image(tag)["Config"]["ExposedPorts"]
code, body = conteneur.repondre("/health")
assert conteneur.utilisateur() != "0"
```

The learner reaches the result by whatever path they like. We query the engine,
never a history.

### A test that is true before the work

This is the most common defect in the field. "Docker answers", "the application
starts", "the file exists": all true before the learner touched anything,
because the setup made them true.

> Before writing a test, ask: "would it be green if the candidate did nothing?"
> If so, it is not a test, it is an assumption of the setup.

The right form is to **merge** that half into the final test, where it can only
be reached after the work. In `images-premiere-image`: "the application answers"
is true from the first check; joined with "with no network at all", it tells a
self-contained image from one that downloads at startup.

### A test that measures too early

A service in a container is not listening the second the container exists.
`Conteneur.repondre()` retries within a bounded budget, and you must use it: **a
false negative is worse than a missing test**, because it fails a learner whose
work is correct.

### A Docker object left behind

Everything a test creates carries the `dsoxlab-<lab>-` prefix and is removed in
`finally`. `conftest.py` provides `image_temporaire`, `conteneur_temporaire` and
`volume_temporaire` so that this is the shortest path.

Two reasons: the prefix rules out any collision with a learner's own image
called "inventory", and systematic removal lets the validator observe that
nothing moved.

### A `doc_url` whose anchor does not exist

The blog's guides are dense: 1095 lines for Swarm, 798 for Compose. A lab
therefore targets the **section** it proves, and that must be verified:

```bash
python3 scripts/verifier-ancres.py --labs
```

`validate-structure --check-urls` does not see this defect: it checks the page's
HTTP status, not the fragment. A wrong anchor gives a link that answers 200 and
drops the reader at the top of a thousand-line guide.

**Anchors are read, never written from memory.**
`scripts/inventaire-guides.py` extracts them from the blog, and the slug rule is
not the one you would guess: accents are kept, punctuation removed without a
separator.

### A tutorial that gives the solution away

The `README.md` teaches the mechanism on a **neutral example**, with names alien
to the challenge. None of its blocks should copy-paste into `challenge/work`.

### A reconstructed command output

Every output shown to the learner is **captured from a real run**. That rule
already paid off twice on the catalogue's very first page: the layer count of a
demo image was wrong, and Docker's error message four times shorter than the
real one.

### An emoji or an em dash

Forbidden in what the learner reads: scenarios, READMEs, hints, assertion
messages. A hook checks it.

## Three statements never to reproduce

They come from the former repository, and `AUDIT.md` documents them.

- **"Alpine has no vulnerabilities"**. A scan says what its database knows, at
  that moment, of the packages it could identify. A scanning lab must make the
  learner observe that a result is a **dated state**, and its fixture must be
  controlled: never depend on a public image still being vulnerable tomorrow.
- **"Non-root user (optional)"**. A container running as root shares UID 0 with
  the host. Make a case where root hurts actually **fail**; do not check a UID.
- **An NFS volume on `127.0.0.1`** in an "optional" exercise that assumes a
  server nothing installs.

## Choosing the runtime

`shell` by default: the lab runs on the learner's machine, with their engine.
Nobody should provision a machine to play a fundamentals lab.

`vm` only when the lab touches the **daemon**, the **kernel** or **several
hosts**: `daemon.json`, rootless, seccomp, AppArmor, firewall, TLS registry,
full disk, remote contexts, Swarm.

And **never claim** to have validated AppArmor or seccomp in an environment that
does not enforce them.

## Before opening a pull request

```bash
pre-commit run --all-files                      # hooks, commit stage
pre-commit run --all-files --hook-stage pre-push
python3 scripts/valider-labs.py --lab <id>      # 0 then 100, no trace left
```

The first two are mechanical and say **nothing** about whether your lab is
correct. Only the third establishes that.

## Commits

Messages in French, a factual subject saying **what changed and why**, with no
conventional prefix. The body tells what was **measured**, including the
measurements thrown away along the way: they are often worth more than the
result.

## An engine defect is not a catalogue defect

dsoxlab lives in [its own repository](https://github.com/stephrobert/dsoxlab).
A CLI limitation becomes an issue there, never a workaround here.

## Reporting an error in a blog guide

A lab that contradicts its companion lesson has found something. That goes to
the blog, not here: open an issue with the file, the section, what the guide
says, what is true, and the command that shows it.
