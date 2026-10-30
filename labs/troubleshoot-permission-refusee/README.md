# troubleshoot-permission-refusee: three refusals, three causes

## What this lab tests

That "permission problem" is not a diagnosis. Three containers hit a refused
access, and the three causes share no gesture:

| Failure | What refuses | What fixes it |
| --- | --- | --- |
| the mount is read-only | the **mount** | recreate the container |
| the directory's rights shut | the **rights** | align the group |
| the file's mode is missing | the **mode**, from the host | fix it on the host |

The reflex gesture, a wide `chmod` on the three directories, fixes **one** of
them. The other two are untouched, and this lab exists so that this gets
measured instead of asserted.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| Failure | Engine's message | Inspection | Cause |
| --- | --- | --- | --- |
| A | "Read-only file system" | RW=**false** | the mount forbids |
| B | "Permission denied" | RW=**true** | the rights refuse |
| C | code **126** | RW=true | the file's mode is missing |

**The lesson is in the A/B pair.** The two messages already differ, and they
are often read as one. The first accuses the mount; the second says the mount
agrees and that the rights are what refuse. The inspection separates them in
one word, and that word is what the first check asks for.

## Why C ties this lab to the previous one

Its code is the one of the file **found but not executable**, already met in
`troubleshoot-exit-127`. Same code, another cause: here the file comes from a
mount, and **a mount changes no mode**. The file's is the host's, and it will
stay so.

That is why a `chmod` played inside the container is of no use, and why the
container does not stay up long enough to play anything in it anyway.

## The only check in the catalogue that refuses a working solution

Making `perm-b` root fixes its symptom in one option, and the fourth check
forbids it.

This is not a nicety. `donnees-permissions-uid-gid` has already shown the right
answer, which is to align the group with the setgid bit. A troubleshooting lab
accepting the shortcut would undo what a method lab taught, and that is exactly
what a learner keeps: the gesture that made the check pass.

## Why a witness, and why repairing it is forbidden

The third answer is an **exit code**, and a repaired container carries none: it
runs.

`temoin-sans-bit` mounts the same directory and fails the same way. The code is
read from it, the brief forbids repairing it, and a check verifies it stayed
broken. Without that last verification, repairing it would make the question
moot, and the lab would grade a value that no longer exists.

This is the third time this safeguard serves in the section. The rule coming
out of it: **a diagnostic value is never read from the object the repair
modifies.**

## Each repair is proven by its effect

A real write for the first two, the script's trace for the third. Never a
command-line option, which would only say what was typed.

The three expected values, for their part, are read from the containers at
grading time: none is written in the checks.

## The starting state is broken, and that is the repository's rule

The four checks are false before any work. A setup task **verifies** that
`perm-a`'s mount is indeed read-only, that `perm-b` cannot write, and that
neither `perm-c` nor the witness is running: without it, a badly cleaned pass
would leave the lab already solved.

## A cleanup trap, paid in advance

The workshop directory goes away **as a whole**. The three failures live in its
rights and in a file's mode: were it to survive repaired, the three repair
checks would be true on the next pass. Recreating it costs less than putting
each right back, and above all it cannot forget one.

## What the lab does not require

A path. The three values can be found in several ways, and the three repairs
can be done by any means producing the expected effect, root excepted for the
second.
