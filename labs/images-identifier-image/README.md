# images-identifier-image: the tag lies, the digest does not

## What this lab tests

Telling which image is actually running. Not the one the tag announces: the
one the engine really loaded. It is the first move of the whole supply chain,
and the one most often missing, because a tag looks like an identity.

It is graded on the **contents of an answer file**, never on the commands
typed. `docker image inspect`, `skopeo inspect` or a read of the image store
all reach the same state: grading the command would grade a style.

## The trap, and it is built

The setup builds **two different images under the same tag**,
`inventaire:1.0`, one after the other. The second takes the place of the first
without the tag changing by a single character, because that is what a tag
does: it points, it guarantees nothing.

The `LABEL org.opencontainers.image.version` of both images says `1.0`. A
label written **inside** the image is worth no more than the one written
outside, and that is counter-intuitive for anyone new to OCI.

The digest of the first build stays visible in
`/opt/lab-images/digest-v1.txt`. Copying it looks like an answer, and one of
the four checks exists precisely to reject it: it is the negative case the
`conteneurs-11` contract of the course plan asks to turn down.

## What is graded

Four checks of equal weight:

- the announced digest is the one the tag points to **now**;
- that digest is **not** the one of the first build;
- the base image digest is right, and **distinct** from the built image's: an
  image and its base have two identities;
- the platform reads `os/architecture` and matches the image.

## What it does not cover

Publishing to a registry and pulling by digest, which belong to the
`images-distribution` module. Pinning in a Dockerfile or a manifest, which is
a writing move rather than a reading one. Signing, which proves origin where a
digest only proves identity.

## What you are given

A throwaway Debian 13, provisioned by `dsoxlab provision`, with the Docker
daemon running, your account already in the `docker` group, and `skopeo`,
which reads an image **without running it**. Nothing is installed on your own
machine.

## Duration

30 minutes. Hints cost from 10 to 25 points.

The guide: [https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/)
