# internes-cgroups-v2: counting and capping

## What this lab tests

That isolation has **two halves** with nothing in common. A namespace restricts
a **view**; a cgroup **counts and caps**. The preceding lab showed the first,
this one shows the second.

It is the second lab of `conteneurs-isolation`, and together they give the
vocabulary the eight others use.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| Fact | Value |
| --- | --- |
| filesystem of `/sys/fs/cgroup` | `cgroup2fs`, `systemd` driver |
| a container's cgroup | `/sys/fs/cgroup/system.slice/docker-<id>.scope` |
| `--memory 256m` gives `memory.max` | `268435456`, the value **in bytes** |
| container **without** a limit, `memory.max` | **`max`**, not 0 nor a big number |

Also verified, and worth knowing: the container sees **its own limit** in its
`/sys/fs/cgroup/memory.max`. That is how a well-behaved application tunes itself
instead of assuming the machine's memory.

## The third question is the one that surprises

You spontaneously look for a number, and the answer is not one.

The absence of a limit is not a very high limit: it is the **absence of the
notion**. That is what explains how a container without `--memory` can take all
the machine's memory, and it is the incident the scenario tells.

Asking it rather than asserting it is deliberate: seeing that file's content for
yourself teaches better than a sentence.

## No value is hardcoded

Not in the tests, not in the solution, not even `max`.

The path is built from the identifier the engine gives, and every expected limit
is **read in the cgroup**, not copied from the brief. A test carrying
`268435456` would be wrong the day the setup changed its limit, and the lab
would die of an unrelated change.

The solution applies the same rule, and that is what makes it a demonstration:
it reads the third answer instead of writing `max`.

## The path is built, not searched for

The engine gives the full identifier, and the `systemd` driver derives a
predictable path from it.

A `find` in `/sys/fs/cgroup` would work too, more slowly and **less safely**:
two containers can share an identifier prefix, and a `find` on a prefix would
then return the neighbour's cgroup.

## The precondition that avoids accusing the learner

On a machine using cgroup v1, the paths and file names differ. The four checks
would fail while talking about limits, when the cause would be the mechanism's
version.

So a guard verifies `cgroup2fs` before any measurement, and **says so**. The
setup makes the same check, which stops the lab before setting it rather than
during grading.

## Why two limits on `bride`, and not one

A single one would suggest that memory is the subject. It is only an example.

The number of processes protects against a **different** failure: the one that
fills the machine's process table, where a memory limit would change nothing.
Both are verified in the cgroup and not in `.HostConfig`: what the option asked
for is not what the kernel applies.

## Elevation is indispensable here

`lab_host()` opens the machine with `sudo=true`, and that is not a convenience:
a container's cgroup files are not readable by an ordinary account.

## The starting state is broken, and that is the repository's rule

| Laid down by the setup | Starting state | Expected move | Check |
| --- | --- | --- | --- |
| `reponses.txt` | three keys, three **empty** values | fill them in | 1, 2 and 3 |
| `mesure` and `libre` | running, one capped one not | leave them alone | all |
| *nothing* | `bride` absent | start it with two ceilings | 4 |

A setup task **verifies** that state: `mesure` does carry a limit, `libre` has
none, and `bride` does not exist yet.

## What the cleanup does not have to do

Clean up the cgroups. The kernel removes a container's cgroup when the container
disappears, which is a difference from volumes and networks. A lab about cgroups
cannot leave debt on the machine.

It does remove `bride`, which the setup does not create: the learner starts it,
and leaving it would make the fourth check true on the next pass.

## What the lab does not require

A path. The values can be read through `cat` as well as through `docker exec`
from the container itself, and both limits are set at the container's creation,
however it is created.
