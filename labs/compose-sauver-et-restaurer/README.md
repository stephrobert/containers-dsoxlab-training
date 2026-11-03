# compose-sauver-et-restaurer: back up a stack, and prove it

## What this lab teaches

That a backup does not exist until you have restored it. The work is not to
produce archives, it is to bring the stack back up elsewhere and show the data
served is the same.

## Why this lab exists

It replaces `donnees-postgres-sauvegarde` alongside lesson C32, for a reason of
principle: **a lab requires only what the lesson teaches**.

The previous lab asked for a PostgreSQL installed on the VM, a
`sudo -u postgres`, a `CREATE DATABASE`, a `COMMENT ON DATABASE`, a
`pg_restore --no-owner --no-privileges` and an `scp` to a second host. Lesson
C32 says nothing of any of that: it teaches backing up and restoring **a Compose
stack**. A lab that requires what the lesson has not introduced no longer
measures learning, it measures resourcefulness, and it fails the learner who did
follow the course.

This one asks for nothing outside the lesson: `pg_dump -Fc`, archiving a volume
through a container and `tar`, archiving the configuration, then `create`, the
files, `up -d --wait`, `pg_restore`.

## The stack is supplied, and that is deliberate

The learner is handed a stack that **works**: a PostgreSQL database with its
file-based secret, and a web front serving a volume of plates. Asking them to
write it would grade the previous module.

So there is **no failure to find**, and that is what makes the lab hard: there is
a proof to produce.

## How the restore is proven, and why not otherwise

By **fingerprint**, not by the presence of a backup file.

| what is compared | why it is not something else |
| --- | --- |
| `count` **and** `md5` of the aggregated content, ordered by id | a table filled with wrong values has the right number of rows |
| `sha256sum` of every plate served | a volume whose files were recreated by hand has the right number of files, not the right bytes |

The order inside the aggregation is not a detail: without `order by`, two
identical databases would return two different fingerprints, and the check would
refuse correct work.

Two values are **drawn at random on every run**, one in the database and one in
a plate. They exist nowhere but in the source: a fingerprint frozen into a
public repository would be a published answer.

## The three traps it sets, and they are in the lesson

**A hot copy of the database volume is not a backup.** It looks complete, it
holds an intermediate state, and it restores without an error until the day it
does not. The check does not look at how the archive was made, it looks at what
it **is**: `pg_restore --list` reads it back, or it is not a logical backup.

**`docker compose exec` swallows the rest of a script.** It reads its standard
input, so the lines that follow never run. This lab's own setup carries
`< /dev/null` for that reason: the trap bites the author as much as the learner.

**Restoring onto a full database fails.** `pg_restore` exits with an error on
`already exists`, and that is good news: it refuses to write over. That is why
the target is **fresh**, and why the order of the steps matters.

## Why `create` before `up`

`docker compose create` creates the containers **and their volumes** without
starting anything. That gives you an empty volume to pour the plates into
**before** the web front serves it. Pouring them in after `up -d` leaves a
service that has already mounted an empty volume.

## The decisive check

**The data the target serves must equal the data the source served.**

A restore that serves wrong data is worse than a restore that fails: a failure
is seen and done again, wrong data is discovered the day it is needed. No total
makes up for it.

## What the lab does not measure

The commands typed. The archive names. The target's port. The exact order of the
steps, as long as the final state is right.

And it does not measure transferring to another machine either: the lesson
mentions it in one sentence without teaching it, so the lab does not ask for it.

## After the lab

`dsoxlab clean` removes **both** Compose projects, the source the setup put in
place and the target the learner created. The lesson's images stay: they come
from a public registry, they serve the machine's other Compose labs, and
removing them would cost a re-download for an object the learner did not ask
for.
