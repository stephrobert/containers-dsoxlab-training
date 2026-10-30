# donnees-volumes-et-montages: where data survives

## What this lab tests

That there are three ways to give a container a file space, that they do not
serve the same purpose, and that **none of the three is the container's layer**,
where everything ends up by default.

| Mount | What it gives | What for |
| --- | --- | --- |
| named volume | a space managed by the engine, which survives the container | data |
| bind mount | a directory of the host, as it is | a provided configuration |
| tmpfs | memory, which persists nothing | a working space |

## A measurement changed how the tests are written

A **tmpfs does not appear** in `.Mounts`. It lives in `.HostConfig.Tmpfs`.
Measured on `docker.lab` on 2026-10-30.

A test that had looked for it in `.Mounts` would have failed whatever the
learner did, and would have accused a blameless learner. That is the kind of
detail you do not guess and have to measure before writing.

## The check that carries the lesson, and the mistake it first made

The fourth. `historique.log` was written by the setup into the container's
**layer**, with a content drawn at random: it exists nowhere else. Getting it
onto the volume presupposes having taken it out **before** destroying the
container, and that is exactly the move that saves or loses data in production.

**A first version of this test passed before any work.** It read
`/var/lib/donnees/historique.log` inside `archive`, where the layer already
carries the file at that path: it measured the file's presence, not its
migration. `valider-labs.py` caught it by returning 1/4 on the starting state,
which is precisely what the zero-score rule is for.

The test now mounts the volume in a **throwaway container**: it measures the
volume, not what `archive` gives to see.

## Why a fingerprint, and not the content

The test compares the SHA256 of the file that arrived on the volume with the one
the setup recorded.

Keeping the content on the host would hand over the answer; keeping the
fingerprint allows verification while revealing nothing, and **the learner can
use it to check themselves**. A check you can verify yourself teaches; an opaque
check makes you guess.

It also rules out the most tempting false success: a file recreated by hand has
the right name and not the right content, which is exactly how one tells oneself
a migration succeeded.

## Each mount is measured twice

What the inspection **declares**, and what the container **can do**.

The clearest case is the read-only bind: the declaration can say one thing and
the machine do another. A lab reading only the declaration would validate a
read-only mount that is not one, which is worse than checking nothing.

## A warning rather than a trap

The brief says plainly that the file is irreplaceable and that there is no
recovery. That is not misplaced kindness: the lesson is in the **order of the
moves**, not in the surprise.

A warned learner who destroys the container anyway has learned something about
themselves. An unwarned learner would only have learned that the lab is unfair.

## The starting state is broken, and that is the repository's rule

| Laid down by the setup | Starting state | Expected move |
| --- | --- | --- |
| `archive` | **no** mount | recreate it with all three |
| `historique.log` | in the layer | get it onto the volume |
| `coffre-donnees` | exists, carries `marque.txt` | mount it in the right place |
| `reference/` | on the host | expose it read-only |

A setup task **verifies** that state before handing over: the container has no
mount, its history is indeed in its layer, and the volume does not carry it yet.

## What the cleanup must remove

The **volume**. A volume survives its container, which is its whole point and
also what makes it dangerous here: if it remained with `historique.log` inside,
the fourth check would be true on the next pass before any work, and the lab
would grade yesterday's work.

`docker volume rm` refuses a volume still used by a container, even a stopped
one: so the container goes first.

## What the lab does not require

A path. The file can come out through `docker cp` as well as through a
redirection of `docker exec`, and get onto the volume through a throwaway
container as well as through a direct write to its host directory. Only the
state counts.
