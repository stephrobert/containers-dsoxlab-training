# One image, four demands, two architectures

The `deux-arch:1.0` image works. It weighs about 200 MB, its `Dockerfile` is a
single stage, the private repository token goes through an `ARG`, and it only
exists for one architecture.

**This is a chaining test.** The four moves were seen separately along the
course; here they have to come together in **one single image**. A light image
whose secret has leaked is worth nothing, and a clean image that serves only one
architecture does not deploy.

## What is expected at the end

The four demands are measured by **six checks of equal weight**: two of them
carry two checks each, because each has two sides. A slimmed image must deliver
the business payload **and** stay under the threshold; a secret must not leak
**and** must have been used.

1. The **published** image contains neither the compiler nor the base image's
   package manager, and running it serves the business workload.
2. Its size stays **under the threshold** this lab measured on this machine, by
   building a multi-stage reference of its own.
3. The token appears **neither in the layers nor in
   `docker history --no-trunc`**. This is the one demand that **no total makes
   up for**: if the secret leaks, the exercise is refused whatever the score.
4. The **private dependency** is present in the image, which is only possible if
   the token was **used**. Removing the token without using it costs this check,
   and this check only: it is not a leak.
5. The lab's registry, on `127.0.0.1:15002`, serves an **index** carrying
   `linux/amd64` **and** `linux/arm64`, and **both of them run**.
6. The **index's** digest is recorded in `/opt/lab-deux-arch/digest.txt`, on a
   single line, in the form `sha256:...`.

**Emulation of foreign architectures is already in place**: this lab set it up.
You do not have to install it.

The full brief is also on the machine, in `/opt/lab-deux-arch/MISSION.md`.

## Three points so you do not look in the wrong place

**The binary can be compiled statically**, and an image whose binary is static
needs no system around it: no compiler, no package manager, no shell. That is the
route which satisfies the first demand without contortion, because a base image's
package manager is always present in it.

**The token is used to produce the dependency**, and in this lab the dependency
**is** the token's digest, its first sixteen characters. This is said plainly: a
real network repository would change nothing about what is measured, which is
that the secret was **used** and did not **leak**.

**The published index carries more than two entries.** The build tool adds its
attestations, which appear as `unknown` platforms. That is normal, and the check
looks for both architectures **among** the entries.

## How you are graded

Six checks of equal weight, and **only the final state counts**. The checks
apply to **the image pulled from the registry**, not to a local image: pushing
without keeping anything locally is the normal way to do it, and the test must
not punish it.

The pass mark is **75 out of 100**. One requirement is made up for by no total:
**the token readable in the history fails the test**, even with everything else
in place. A `--build-arg` leaves its value there, and anyone who pulls the image
reads it back. The image itself looks clean, which makes this the most discreet
leak in the trade.

Four hints are available, and **they cost points**: `dsoxlab hint`.
