# Test: rebuild an image for two architectures

An image that works, in a single stage, with its compiler, its token in the
history, and one architecture. All of it has to be redone **in one single
image**.

## The six checks

They are of equal weight, and each rests on a verifiable fact. **They apply to
the image pulled from the registry**, because pushing without keeping anything
locally is the normal way to do it.

### 1. Neither compiler nor package manager in the published image

They only served to build, and they then travel to everyone who pulls the image.

**And the business workload succeeds.** Removing the compiler is easy; removing
it while keeping a working binary is the multi-stage move. A binary linked
dynamically against libraries left in the build stage does not start: that is the
classic mistake.

### 2. Size under the measured threshold

The threshold comes from a **multi-stage** reference build made on this machine
during `dsoxlab run`. It is not written into the test: a hard-coded size would
expire at the first update of the base image.

### 3. The token nowhere

**This is the critical requirement, and the only one: no total makes up for
it.**

Two distinct places. **The history**: a `--build-arg` leaves its value there, and
anyone who pulls the image reads it back. Measured on this test's bench: two
occurrences with `--build-arg`, zero with a mounted secret. **The layers**,
because a secret written to a file then deleted still travels in the layer that
carried it.

### 4. The private dependency is the repository's

Removing the token without using it gives a clean, useless image: the dependency
can only be right if the secret was **used**.

This check was an assertion of the previous one, and it was taken out of it. A
learner who removed the token without using it shipped a clean image, kept 83
points, and was refused by a check that talks about a **leak** when nothing had
leaked. **Losing this check costs its points, and nothing more.**

### 5. The index carries both architectures, and both run

The check looks for `amd64` and `arm64` **among** the manifests, without
requiring a count: the build tool adds its attestations, which appear as
`unknown` platforms.

**And both run.** An index that declares a platform whose image does not start is
worse than a single-platform index: it promises a deployment that will fail for
whoever relies on it.

### 6. The recorded digest is the index's

That is the distinction this check exists to measure. The index has its own
digest, and that is the one you pin: it designates both architectures at once and
lets the receiving engine pick its own. One image's digest designates **one**
platform, and a deployment pinned on it fails everywhere else.

If you record an image's digest, the message will say so: that is the instructive
mistake, and naming it is better than reporting a difference.

## The marking

Six checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
