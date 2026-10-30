# What is asked

On `docker.lab`, a throwaway Debian 13 with Docker running and `skopeo`
installed.

The `inventaire:1.0` tag was built **twice** on this machine. The second build
took the place of the first, without the tag changing by a single character.
You have to say what is actually running.

## 1. The digest of the image the tag points to today

The one of the **second** build, the only image `inventaire:1.0` now points
to.

The digest of the first one is still lying in
`/opt/lab-images/digest-v1.txt`. Copying it is rejected: it is the surface
answer, and one check exists for it.

## 2. The digest of the base image

The one of `debian:13`, as it is on this machine. It is **distinct** from the
built image's: an image and its base have two identities, and mixing them up
is the mistake this point measures.

## 3. The platform of the image

As `os/architecture`, for instance `linux/amd64`. It is read off the image, not
guessed from the machine.

## 4. Write the answer

Three lines in `/opt/lab-images/reponse.txt`, with no space around the equals
sign:

```text
digest=...
base=...
plateforme=...
```

Blank lines and `#` comments are tolerated, the order is free: the content is
graded, not the layout.

## What is not looked at

**No command is graded.** `docker image inspect`, `skopeo inspect` or a read of
the image store all reach the same state. A route different from ours that
reaches the same result is worth just as much.

A `LABEL org.opencontainers.image.version` proves nothing either: both images
claim `1.0` on the inside. A label written inside the image is worth no more
than the one written outside.

## Verify

```bash
dsoxlab check images-identifier-image
```
