# An image changed under your tag

## The situation

The team ships an inventory API under the tag `inventaire:1.0`. That tag has
not moved in three weeks, and that is exactly what reassures everyone: the
version is frozen, so the image must be frozen too.

Last night, production started writing a file nobody recognizes. The tag still
reads `1.0`.

On this machine, `inventaire:1.0` was built **twice**. The second build took
the place of the first, without the tag changing by a single character. That is
the normal behaviour of a tag: it points, it guarantees nothing. The
`LABEL org.opencontainers.image.version` of both images announces `1.0` either
way, because a label written inside an image is worth no more than the one
written outside it.

## The objective

Say exactly which image is running, and prove it by something other than its
name.

Write three lines into `/opt/lab-images/reponse.txt`, one per entry, with no
space around the equals sign:

```text
digest=<the digest that inventaire:1.0 points to today>
base=<the digest of the debian:13 image as it stands on this machine>
plateforme=<os/architecture of inventaire:1.0>
```

## What is graded

Four checks of equal weight, and none of them looks at your commands:

- the **announced digest** is the one the tag points to now;
- that digest is **not the one of the first build**, whose trace is still
  sitting in `/opt/lab-images/digest-v1.txt`. Copying it looks like an answer
  and measures nothing;
- the **base image digest** is correct, and distinct from the built image's: an
  image and its base have two identities;
- the **platform** has the `os/architecture` shape and matches the image.

A path different from ours that reaches the same result is worth just as much:
what is graded is the state of your answer file, not the way you got there.

## What you have

A Debian 13 host with the Docker daemon running, your account already in the
`docker` group, and `skopeo`, which can read an image **without running it**.

## Two hints, if you get stuck

The digest of a local image is not found in its tag: it lives in the metadata
the daemon keeps about it. Any command that can inspect an image can print it.

A digest starts with an algorithm name followed by a colon. If your answer has
none, you have probably copied something else, such as a short identifier
truncated for display.
