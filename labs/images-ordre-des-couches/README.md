# images-ordre-des-couches: a correct Dockerfile, and an expensive one

## What this lab tests

That the order of a Dockerfile's instructions decides what the cache can serve,
and that **the defect is invisible**: the image produced is correct either way.
Only its rebuild cost changes.

That is what makes this defect so widespread. Nothing looks broken, so nothing
seems to need fixing, and continuous integration takes six minutes to redo work
that nobody modified.

## Measured before being written

On `docker.lab`, on 2026-10-30, on the same context with two orders:

| Order | code changed | manifest changed |
| --- | --- | --- |
| copy the context then install | work **redone** (3 s) | redone |
| manifest, install, then code | **served by the cache** (1 s) | redone |

And the naive answer was **put to the test**: the starting Dockerfile, built as
it stands under the expected name, scores **2/4**. The two green checks are the
ones not bearing on the order, and the two red ones name the cause. A lab whose
naive answer scored 4/4 would measure nothing.

## The fingerprint, and why not the layer identifier

The installation tool draws sixteen random bytes and writes them into the
image. Two images carrying the **same** fingerprint did not replay the
instruction: the layer comes from the cache.

The first draft of these tests compared the layer identifiers from `docker
history`. Measured the same day: under buildkit they all read `<missing>` for
intermediate layers, and the comparison concluded "reused" on work that had
been redone. **An indicator returning the same value everywhere measures
nothing**, and it concluded green.

## Why the expensive work does not depend on the network

`installer` is a tool laid down in the base image: it reads the manifest and
sleeps one second per line.

A lab doing a real `apt-get` or `pip install` would measure the day's bandwidth
and would fail on a machine without outbound access **while blaming the
learner**. The cost is simulated, and it is real: three seconds are enough to
make the gain visible.

## Why both halves are graded

The cache must serve when the code changes, and it must **stop** serving when
the manifest changes.

Copying the manifest after the installation would make the third check green
and have the cache serve even when the dependencies change: the image would
stay frozen on the old ones, and nobody would see it before production. A check
looking only at the first half would therefore reward the costlier of the two
faults.

The fourth one also verifies that the new dependency is **really installed**:
redoing work with no effect would otherwise pass for a success.

## Why the draft is in the context

A copy of the whole context does not copy "the code", it copies **everything**,
the Dockerfile included. Those files swell the image, and above all each of them
invalidates the cache when it changes: editing the Dockerfile would be enough
to redo the installation.

The check does not say how to exclude them. An exclusion file and a targeted
copy give the same state, and it is the state that is graded.

## Why the checks rebuild in a copy

Modifying the learner's directory in order to grade it would be doubly wrong:
it would destroy their work, and the verdict would bear on a state the test
produced itself.

The modification is an **append at the end of a file**: the code stays
executable, the manifest stays readable, and the image stays buildable.

## The starting state is broken, and that is the repository's rule

The setup **does not build** the image: the four checks are therefore false
before any work, including the ones not bearing on the order. Building is part
of the mission.

A setup task verifies that the base exists, that the learner's image does not,
and that the starting Dockerfile does carry the wholesale copy: without it, a
badly cleaned pass would leave the lab already solved.

## A cleanup trap, paid in advance

**The build cache has to go with the rest.** A build's intermediate layers are
not images: they live in the builder's cache, and a `docker image prune` does
not touch them. Without a `builder prune`, the next pass's build would be served
by a cache the learner did not write a line of, and the lab would measure work
that did not happen.

It is the slowest purge in the catalogue, and it is the price of
reproducibility.

## What the lab does not require

A path. The token is drawn by the setup and read back from the source at grading
time; the dependencies are read back from the manifest. Nothing is hard-coded in
the checks, and nothing is graded on a form.
