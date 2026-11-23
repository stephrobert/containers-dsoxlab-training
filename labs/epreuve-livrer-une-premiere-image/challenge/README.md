# Deliver a first image worth publishing

A small application is waiting to be delivered. It lives in
`/opt/lab-premiere-livraison`, with everything its author left there: its code,
its dependency, the credentials file they used to fetch their packages, and the
working directory where they piled up their extracts.

**There is no Dockerfile.** Writing it is your job.

The lab's registry is already running on `127.0.0.1:5000`. It accepts HTTP
because it listens on the loopback interface: there is nothing to configure on
the daemon.

## What is expected at the end

1. The **`premiere-livraison:1.0`** image exists, and
   `docker run --rm premiere-livraison:1.0`, **with no identity option at
   all**, serves the line `inventaire=` followed by the value in the
   `donnees/reference` file.
2. The image **does not run as root**: the user it declares is a **numeric
   non-zero UID**, and the data directory inside the image **belongs to it**,
   without being world-writable.
3. Neither the `.identifiants` file, nor its token, nor the contents of
   `travail/` are present in **any layer** of the image.
4. What the image **adds to its base** stays under the budget this lab
   measured on this machine, by building a reference of its own during
   `dsoxlab run`. **No base is imposed**, and the one you pick does not count:
   only what you put on top of it does.
5. The image is **published** in the lab's registry, and the **digest the
   registry serves** is recorded in
   `/opt/lab-premiere-livraison/digest.txt`, on a single line, in the form
   `sha256:...`.

The full brief is also on the machine, in
`/opt/lab-premiere-livraison/MISSION.md`.

## Two points that matter

**The UID is yours to choose**, as long as it is numeric and non-zero. What is
measured is not the number, it is that it be numeric: a user name only resolves
inside the image that defines it, and an orchestrator does not read its
`/etc/passwd`.

**The size budget is not an optimisation exercise.** It is generous, and the
gap it measures is the size of what was delivered without any reason to be.
Measured on this machine: the application content adds 0.1 MB to its base
whatever that base is, and delivering the working directory adds 80.

## How you are graded

Six checks of equal weight, and **only the final state counts**. No Dockerfile
instruction is imposed: two ways of obtaining the same image get the same mark.

The pass mark is **75 out of 100**. One requirement is made up for by no total:
**the token present in a layer fails the test**, even with everything else in
place. A secret delivered in an image is a published secret: the image goes into
a registry, others read it, and removing it afterwards takes nothing back.

Four hints are available, and **they cost points**: `dsoxlab hint`.

## Test: deliver a first image

A repository holds an application, its dependency, a credentials file and a
working directory. **There is no Dockerfile**: writing it is your job.

### The six checks

They are of equal weight, and each rests on a verifiable fact.

#### 1. The image answers with no identity option

`docker run --rm premiere-livraison:1.0`, **with no `--user`**, serves the
business value. An image that only runs with an option chosen by the caller is
not deliverable: whoever receives it does not know that detail.

#### 2. A numeric non-zero UID that owns its data

**Numeric**, not a name: a name only resolves inside the image that defines it,
and an orchestrator does not read its `/etc/passwd`. It is the only form a third
party can verify.

And the data directory **belongs to it**, without being world-writable.
Declaring a non-root user and leaving them a directory they do not own delivers
an image that fails on its first write; making it world-writable fixes the
symptom by cancelling the benefit.

#### 3. The token in no layer

**This is the critical requirement: no total makes up for it.**

The check reads **the image's archive**, not its filesystem. A `RUN rm` that
erases a secret at a later step leaves the layer that carried it intact: the
file is gone from the final view, and it still travels with the image. Looking
inside the container would see nothing and would declare clean an image that is
not.

And it is the **value** of the token that is searched for, not the file's name:
renaming changes nothing about the secret travelling.

It is about **that single fact**. A published secret cannot be taken back, and
it is the fault this test exists to eliminate.

#### 4. The working directory is not delivered

Waste, not a breach: this check is graded and it **can be made up for**. Work
files weigh down the image for everyone who pulls it, forever, which is a fault,
but one that can be redeemed.

#### 5. What the image adds to its base

**No base is imposed**, and yours does not count: the check compares what you
put **on top** with what a reference image puts on top of its own, plus a
margin.

Measured on this machine: the same application content adds 0.1 MB to
`alpine:3.22` and to `debian:13-slim` alike, and delivering the working
directory adds 80. That gap is what the check sees, not the size of your base.

The margin is generous. The test measures "did not deliver what has no business
being in an image", not "optimised to the megabyte", which is the subject of
another test in the path.

#### 6. Published, and the recorded digest is the one served

The digest is **asked of the registry**, then compared with yours. A tag can be
rewritten: two `push` of the same tag serve two different images. The digest is
the only identity a third party can demand.

And matching is not enough: the image is **pulled by that digest**, then run
with no identity option, and it must serve the business value. That is what
whoever receives the delivery does, played for real: comparing two strings
proves you copied the right digest, not that the digest gives anything.

### The marking

Six checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**: no Dockerfile instruction is imposed.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
