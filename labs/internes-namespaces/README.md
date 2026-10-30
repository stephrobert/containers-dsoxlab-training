# internes-namespaces: a view, not a wall

## What this lab tests

That a namespace is a **view**, not a barrier. A container's PID 1 is an
ordinary process of the host, under another PID, with its command line
readable. Nothing is hidden from the host: only the container has a restricted
view.

It is the first lab of the `conteneurs-isolation` section, and it establishes
what the nine others assume.

## The security lesson, measured before being written

On `docker.lab`, on 2026-10-30:

| namespace | isolated from the container |
| --- | --- |
| `pid`, `net`, `mnt`, `uts`, `ipc`, `cgroup` | yes |
| **`user`** | **no, shared with the host** |

`user:[4026531837]` is identical on both sides. Consequence: user 0 in the
container is user 0 on the machine.

That is not a flaw, it is the default setting, and it is what makes necessary
all the precautions the next section teaches. The lab makes that namespace be
**found** rather than announced, because you only properly distrust what you
have seen for yourself.

## No value is written into the tests

The PID is asked of the engine, the namespace identifiers are read from
`/proc`, and the shared namespace is found **by comparison**.

That is a decision, not a convenience: the day Docker enables user isolation by
default, the third check will **follow** instead of becoming wrong. A list
written in advance would have turned a measurement into dogma.

The reference solution applies the same rule, and that is what makes it a
demonstration of method: it looks for the shared namespace by comparing all
seven, instead of writing `user`.

## The fourth check looks at the effect, not the option

Reading `.HostConfig.PidMode` would be simpler and would grade the
**intention**. Verifying that the container sees its neighbour's process grades
the **result**, and accepts any path that leads there.

It also verifies the PID it sees it under: the **host's**. That is what
distinguishes "it sees the host's processes" from "it sees its own", which
nothing else separates, since both give a non-empty list.

## Why the container's command is a marker

`sleep 987654` is of no use to the container. It exists to be recognisable in
the host's process list, where it appears as it is, and the brief names it.

Looking for a needle without knowing what it looks like would teach nothing
about the subject: the subject is that the needle **is visible**, not that it is
hard to find.

## Elevation is indispensable here

`lab_host()` opens the machine with `sudo=true`, and for once that is not a
convenience: the links in `/proc/<pid>/ns/` are only resolvable by root. A lab
that had measured without elevation would have returned empty strings and
accused the learner.

## The starting state is broken, and that is the repository's rule

| Laid down by the setup | Starting state | Expected move | Check |
| --- | --- | --- | --- |
| `reponses.txt` | three keys, three **empty** values | fill them in | 1, 2 and 3 |
| `cloisonne` | running, isolated | leave it alone | all |
| *nothing* | `indiscret` absent | start it with the host's view | 4 |

A setup task **verifies** that state before handing over: `cloisonne` is running
with its marker, and `indiscret` does not exist yet.

## What the cleanup removes, although the setup does not create it

`indiscret`. The learner starts it, and leaving it behind would make the fourth
check true on the next pass before any work.

Nothing else to clean, and that is worth noting: this lab creates no volume, no
network, no image. It only looks, which is exactly its subject.

## What the lab does not require

A path. The PID can be read from the engine as well as from the host's process
list; the namespaces through `readlink` as well as `lsns`; and the view of
processes is obtained at the container's creation, however it is created.
