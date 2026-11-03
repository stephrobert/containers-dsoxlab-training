# epreuve-reconstruire-une-image-pour-deux-architectures: the chaining test

## What this test measures

That **one single** image meets four demands that were seen separately. It closes
the "Build advanced images" module and re-explains nothing.

Its `lab_type: challenge` is what allows its `exam_passing_score`, set to **75**.
The six checks are of equal weight, and one of them is critical.

## Its overlap is assumed, and that is what justifies it

Four training labs already measure its moves, and two are tests themselves:

| Move | Already measured by |
| --- | --- |
| two-platform index, both run, index digest | `images-multi-architecture`, already a challenge |
| secret absent from layers and history | `buildkit-secret-de-build`, already a challenge |
| multi-stage | `images-build-multi-etapes` |
| size | `images-optimiser-la-taille` |

The overlap was reported and put to arbitration before writing, then assumed on
2026-11-02. The reason is that **none of the four measures the chaining**. And
chaining is what counts in production: a light image whose secret has leaked is
worth nothing, and a clean image that serves only one architecture does not
deploy.

## What the bench established before writing

Four points were uncertain, and each could have made the test unwritable. All
were measured on 2026-11-02:

- **`--build-arg` leaves the token in the history**: two occurrences. That is the
  delivered defect, and it is real;
- **`--mount=type=secret` leaves none**, neither in the history nor in the
  layers, and the dependency is produced. That is the fix, and it is measurable;
- `buildx` pushes an OCI index, and **both architectures run under emulation** on
  this amd64 VM;
- **the index carries four manifests, not two**: `buildx` adds its provenance
  attestations, which appear as `unknown` platforms.

The last point changed the check: it looks for `amd64` and `arm64` **among** the
manifests, instead of requiring exactly two. A check counting the entries would
refuse the tool's normal output.

## Why the checks apply to the image pulled from the registry

Because `buildx` with a registry output **leaves nothing locally**. Requiring a
local image would punish the normal way of publishing, and the test grades the
final state.

It is also fairer: we measure what is **delivered**, not what stayed on the
builder's own machine.

## Why the private dependency is the token's digest

A real private repository would need one more network service, and the bench
showed that a build `RUN` can reach it through its bridge address. But what is
**measured** would not change one bit: that the secret was **used**, and that it
did not **leak**.

The digest proves both without adding a part, and the brief says so plainly
rather than pretending. A lab that simulates must say that it simulates.

## The critical requirement, and why it is the trade's most discreet leak

**The token readable in the history fails the test**, even at 83 points.

It is discreet because the image itself contains nothing suspicious: you can
inspect it, list its files, open a shell inside, and see nothing. The value is in
the build metadata, which `docker history --no-trunc` displays and nobody looks
at.

## What this lab gives back to the machine

Everything it set up, and two parts deserve a mention:

- **the buildx builder**, which is a container holding the build cache for every
  platform. Leaving it would occupy several hundred megabytes;
- **emulation is NOT removed**, and that is deliberate. It comes from Debian
  packages and a systemd unit, not from an engine object: uninstalling it would
  touch the machine more deeply than the lab did, and
  `images-multi-architecture` needs it too.
