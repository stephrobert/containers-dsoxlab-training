# Test: deliver a first image

A repository holds an application, its dependency, a credentials file and a
working directory. **There is no Dockerfile**: writing it is your job.

## The five checks

They are of equal weight, and each rests on a verifiable fact.

### 1. The image answers with no identity option

`docker run --rm premiere-livraison:1.0`, **with no `--user`**, serves the
business value. An image that only runs with an option chosen by the caller is
not deliverable: whoever receives it does not know that detail.

### 2. A numeric non-zero UID that owns its data

**Numeric**, not a name: a name only resolves inside the image that defines it,
and an orchestrator does not read its `/etc/passwd`. It is the only form a third
party can verify.

And the data directory **belongs to it**, without being world-writable.
Declaring a non-root user and leaving them a directory they do not own delivers
an image that fails on its first write; making it world-writable fixes the
symptom by cancelling the benefit.

### 3. Neither the token nor the work files in any layer

**This is the critical requirement: no total makes up for it.**

The check reads **the image's archive**, not its filesystem. A `RUN rm` that
erases a secret at a later step leaves the layer that carried it intact: the
file is gone from the final view, and it still travels with the image. Looking
inside the container would see nothing and would declare clean an image that is
not.

And it is the **value** of the token that is searched for, not the file's name:
renaming changes nothing about the secret travelling.

### 4. Size under the measured threshold

The threshold comes from a **reference build made on this machine** during
`dsoxlab run`. It is not written into the test: a hard-coded size would expire
at the first update of the base image, and the lab would start rejecting correct
work.

The margin is generous. The test measures "did not deliver what has no business
being in an image", not "optimised to the megabyte".

### 5. Published, and the recorded digest is the one served

The digest is **asked of the registry**, then compared with yours. A tag can be
rewritten: two `push` of the same tag serve two different images. The digest is
the only identity a third party can demand.

## The marking

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**: no Dockerfile instruction is imposed.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
