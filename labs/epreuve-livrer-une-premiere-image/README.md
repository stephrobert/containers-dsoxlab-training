# epreuve-livrer-une-premiere-image: the build module's test

## What this test measures

Writing a Dockerfile that delivers an image you can publish without blushing. It
closes the "Build and publish an image" module and re-explains nothing.

Its `lab_type: challenge` is what allows its `exam_passing_score`, set to **75**.
The five checks are of equal weight, and one of them is critical.

## What the repository holds, and why each piece is there

| Piece | Should it go into the image? | What it measures |
| --- | --- | --- |
| `app.sh` | yes | without it, the image answers nothing |
| `donnees/reference` | yes | an image that starts without its data serves its own error code |
| `.identifiants` | **no** | the critical requirement: a delivered secret is a published secret |
| `travail/`, 40 MB | **no** | the size threshold sees it, and that is the measured way to prove it |

The forty megabytes come from `/dev/urandom`, hence **incompressible**: an image
carrying zeroes would compress, and the size check would no longer measure
anything.

## Why the size threshold is measured, not written

The `run` builds a **reference** image with a correct Dockerfile, records its
real size on this machine, deletes the image, and records the threshold. The
reference Dockerfile lives in `/root` and is erased right after: it carries the
answer.

A size hard-coded into the test would expire at the first update of the base
image, and the lab would then start **rejecting correct work**. That is the kind
of flaw that makes people doubt the machine when it is the lab that is wrong.

## The critical requirement, and why it is measured in the archive

**The token present in a layer fails the test**, even at 80 points.

The check reads `docker save`, not the container. The reason is precise: a
`RUN rm` that erases a secret at a later step leaves **the layer that carried it
intact**. The file is gone from the final view, and it still travels with the
image. A check looking inside the container would see nothing, and would declare
clean an image that is not: it would measure the view, not the content.

And it is the **value** of the token that is searched for, not the file's name:
renaming changes nothing about the secret travelling.

## Why the UID must be numeric

A user name only resolves inside the image that defines it: it lives in its
`/etc/passwd`, which an orchestrator does not read and an admission controller
cannot verify. The numeric UID is the only form a third party can demand, and it
is the one required by policies that refuse `runAsUser: 0`.

The number itself is free: what is measured is not its value.

## It does not duplicate `epreuve-livrer-une-image`

That one closes a later module: it measures delivery to a **bare client**, on
two machines, with a read-only account. This one measures the **first** delivery,
on a single machine.

Both share one requirement, the secret absent from every layer, and that is
deliberate: it is the costliest mistake in the trade, and it is measured every
time you build, not once in a course.

## What the test does not measure

Multi-architecture builds, multi-stage builds, fine size optimisation. Those are
the subjects of later tests.
