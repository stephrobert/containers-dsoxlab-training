# Two containers refuse to start, for two reasons

## The situation

A deployment fails. Two services do not start, and both messages mention a
port. You relaunch, it fails the same way. You relaunch again, and this time the
message **changes**: it now mentions a name already in use.

You think you broke something else in the meantime. You spend twenty minutes on
the wrong problem.

Then you look for the first port's culprit, and you find it in one command. You
look for the second one the same way, and **there is nothing**. The container
list is silent, and the port is taken all the same.

## The goal

Make both messages speak. Two containers refused to start, each on an already
taken port, and a third one is there as a witness:

```text
intrus-a        wanted the host's port 18200
intrus-b        wanted the host's port 18201
temoin-refuse   wanted port 18200 too, and you will NOT REPAIR IT
```

**Compare the two error messages** the engine returned for `intrus-a` and
`intrus-b`. They do not say the same thing, and that is the whole key to the
diagnosis: one comes from the engine, which knows what it has already reserved,
the other comes from the system, which refuses to listen.

Fill in the three lines of `/opt/lab-conflit/reponses.txt`:

```text
statut_intrus=<temoin-refuse's STATUS, as the engine declares it>
coupable_a=<the NAME of the container occupying port 18200>
coupable_b=<the NAME OF THE PROGRAM occupying port 18201>
```

For the third one, **do not look on Docker's side**: it shows nothing, and that
is precisely what wastes time. A system tool names it in one line.

The brief is also written to `/opt/MISSION.md`.

## The first question explains the changing message

A refused container is **created all the same**. Its status says so, and it
therefore occupies its name.

That is why the second attempt fails on a completely different message, about a
name already in use: two messages for a single cause, and you look for two
problems. The scenario's twenty minutes are right there.

## The repair, and this is where the lab has an opinion

Both containers must **run**, and publish their port 80 on a host port **other**
than the one that was taken.

And both culprits must still be **there**: the container that runs, and the
host's program that listens.

Freeing the port would be the spontaneous move, and it is the wrong one.
**Nothing said they were useless**, and a taken port is often taken for a
reason. You do not cut a running service to start another one: it is the
newcomer you move.

## What is graded

The **state of the system**. The three expected values are read at grading time,
and none is written into the checks.

The fourth check verifies both halves of the repair: that the intruders run
**elsewhere**, and that the culprits are intact. Without the second, the most
destructive answer would pass, and the lab would teach exactly what to avoid.
